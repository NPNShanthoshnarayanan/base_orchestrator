import json
from typing import Annotated, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from agent_store.constants import GraphConstants, PromptConstants, FieldMeta, OPEN_AI_KEY
from agent_store.tools import get_field_details, get_field_values, get_field_list

load_dotenv()


class ItemGenerationState(TypedDict):
    """State definition for the filter generation graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    context: Optional[Dict]
    field_list: List[Dict]
    field_values_dict: Dict
    values_api_url: str
    generated_code: Optional[str]
    store: Optional[Dict]


class ItemCreationGraph:
    def __init__(
            self,
            flow_id,
            memory_saver,
            thread_id,
            system_prompt: str = PromptConstants.ItemCreationAgent.SYSTEM_MESSAGE,
            model: str = "gpt-4o",
            temperature: float = 0,
            max_retries: int = 3,
            max_tool_iterations: int = 5,
    ):
        """
        Initialize the LangGraph-based filter generation chain.

        Args:
            system_prompt: System prompt for LLM
            model: OpenAI model to use
            temperature: LLM temperature (0 for deterministic)
            max_retries: Maximum retry attempts for failed generations
            max_tool_iterations: Maximum tool call iterations allowed
        """
        self.flow_id = flow_id
        self.memory = memory_saver
        self.thread_id = thread_id
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.max_tool_iterations = max_tool_iterations
        self.retry_from_scratch = False

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model, openai_api_key=OPEN_AI_KEY, temperature=self.temperature
        )

        # Create tools
        self.tools = [get_field_details, get_field_values]

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create tool executor
        self.tool_executor = ToolNode(self.tools)

        # Build the graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)

    def _prepare_context_node(self, state):
        # Add system message if not present
        messages = state.get(GraphConstants.StateKeys.MESSAGES, [])
        if not messages or not isinstance(messages[0], SystemMessage):
            field_list = state.get(GraphConstants.StateKeys.FIELD_LIST, [])
            context = state.get(GraphConstants.StateKeys.CONTEXT)

            context_parts = []

            # Add field list information
            if field_list:
                context_parts.append(GraphConstants.ContextMessages.AVAILABLE_FIELDS)
                for field in field_list:
                    field_info = GraphConstants.ContextMessages.FIELD_INFO_FORMAT.format(
                        name=field.get(GraphConstants.FieldMeta.NAME, GraphConstants.FieldMeta.UNKNOWN),
                        type=field.get(GraphConstants.FieldMeta.TYPE, GraphConstants.FieldMeta.UNKNOWN),
                        id=field.get(GraphConstants.FieldMeta.ID, GraphConstants.FieldMeta.UNKNOWN),
                    )
                    context_parts.append(field_info)

            # Add additional context
            if context:
                context_parts.append(GraphConstants.ContextMessages.ADDITIONAL_CONTEXT_PREFIX + str(context))

            context_msg = "\n".join(context_parts)

            messages = [SystemMessage(
                content=self.system_prompt + "\n\n" + context_msg)] + messages

        return {
            **state,
            GraphConstants.StateKeys.MESSAGES: messages,
        }

    def _generate_node(self, state):
        """
        Generate filter code using the LLM with tools.
        """
        try:
            messages = state[GraphConstants.StateKeys.MESSAGES]

            # Call the LLM with tools
            response = self.llm_with_tools.invoke(messages)

            # Add response to messages
            updated_messages = messages + [response]

            # Update tool iteration count if tool calls are present
            tool_iteration_count = state.get(GraphConstants.StateKeys.TOOL_ITERATION_COUNT, 0)
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_iteration_count += 1

            # Extract code if present in the response
            generated_code = None
            if hasattr(response, "content") and response.content:
                generated_code = response.content

            return {
                **state,
                GraphConstants.StateKeys.MESSAGES: updated_messages,
                GraphConstants.StateKeys.GENERATED_CODE: generated_code,
                GraphConstants.StateKeys.TOOL_ITERATION_COUNT: tool_iteration_count,
            }

        except Exception as e:
            print(f"Generation failed: {e}")
            return {**state, "validation_errors": [f"Generation error: {e}"]}

    def _validate_node(self, state):
        """
        Validate the generated code.
        """
        state = state
        generated_code = state.get(GraphConstants.StateKeys.GENERATED_CODE)
        validation_errors = []

        if not generated_code:
            validation_errors.append(GraphConstants.Validation.NO_CODE_ERROR)
        else:
            # Try to parse as Python
            try:
                cleaned_code = self._clean_code(generated_code)
                field_value_map = json.loads(cleaned_code)
                if isinstance(field_value_map, dict) and state.get(GraphConstants.StateKeys.FIELD_VALUES_DICT) is not None:
                    state[GraphConstants.StateKeys.FIELD_VALUES_DICT].update(field_value_map)
                    field_value_map = state[GraphConstants.StateKeys.FIELD_VALUES_DICT]

                field_list = state.get(GraphConstants.StateKeys.FIELD_LIST, [])
                missed_required_field_list = []
                for field in field_list:
                    if field[FieldMeta.REQUIRED] is True and field[FieldMeta.ID] not in field_value_map:
                        missed_required_field_list.append(field[FieldMeta.ID])
                print(f"{field_value_map=} {missed_required_field_list=}")
                if missed_required_field_list:
                    state["store"].update({"interrupted_message": f"Provide values for this fields {missed_required_field_list=}", "subgraph_id": "item_creater_agent"})
                    user_feedback = interrupt(
                        f"Provide values for this fields {missed_required_field_list=}"
                    )
                    self.retry_from_scratch = True
                    validation_errors.append(GraphConstants.Validation.NO_CODE_ERROR)
                    return {**state, GraphConstants.StateKeys.MESSAGES: [HumanMessage(content=user_feedback)],
                            GraphConstants.StateKeys.FIELD_VALUES_DICT: field_value_map,
                            GraphConstants.StateKeys.VALIDATION_ERRORS: validation_errors}
                else:
                    return {**state,
                            GraphConstants.StateKeys.FIELD_VALUES_DICT: field_value_map,}

            except SyntaxError as e:
                validation_errors.append(f"Syntax error: {e}")
        return {**state, GraphConstants.StateKeys.VALIDATION_ERRORS: validation_errors}

    def _retry_node(self, state):
        """
        Handle retry logic.
        """
        retry_count = state.get(GraphConstants.StateKeys.RETRY_COUNT, 0) + 1
        validation_errors = state.get(GraphConstants.StateKeys.VALIDATION_ERRORS, [])
        tool_iteration_count = state.get(GraphConstants.StateKeys.TOOL_ITERATION_COUNT)
        messages = state.get(GraphConstants.StateKeys.MESSAGES, [])

        # Add error feedback to messages for next attempt
        if validation_errors and retry_count <= self.max_retries:
            error_msg = f"Previous attempt failed with errors: {', '.join(validation_errors)}. Please generate valid Python code"
            messages = messages + [HumanMessage(content=error_msg)]
        elif self.retry_from_scratch:
            self.retry_from_scratch = False
        elif tool_iteration_count > self.max_tool_iterations and retry_count <= self.max_retries:
            messages = [messages[1]]

        return {
            **state,
            "retry_count": retry_count,
            "messages": messages,
            "validation_errors": [],
            "generated_code": None,
        }

    def _creation_node(self, state):
        print(f"state-> {state}")
        return {**state}

    def _clean_code(self, code: str) -> str:
        """
        Clean generated code by removing markdown formatting.

        Args:
            code: Raw generated code

        Returns:
            Cleaned code
        """
        code = code.strip()

        # Remove markdown formatting
        if code.startswith("```python"):
            code = code[9:].strip()
        elif code.startswith("```"):
            code = code[3:].strip()

        if code.endswith("```"):
            code = code[:-3].strip()

        return code

    def _route_after_generation(self, state) -> str:
        """
        Route after generation based on whether tools need to be called.
        """
        last_message = state[GraphConstants.StateKeys.MESSAGES][-1] if state[
            GraphConstants.StateKeys.MESSAGES] else None

        # Check if the last message has tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Check tool iteration limit before routing to tools
            current_count = state.get("tool_iteration_count", 0)
            if current_count > self.max_tool_iterations:
                # Max tool iterations reached, route to retry
                return "retry"

            return "tools"

        # Check if we have generated code to validate
        if state.get(GraphConstants.StateKeys.GENERATED_CODE):
            return "validate"

        # If no code and no tool calls, retry
        return "retry"

    def _route_after_validation(self, state) -> str:
        """
        Route after validation based on whether errors exist.
        """
        validation_errors = state.get("validation_errors", [])

        if not validation_errors and not self.retry_from_scratch:
            return "create"
        else:
            return "retry"

    def _route_after_retry(self, state) -> str:
        """
        Route after retry based on retry count.
        """
        retry_count = state.get("retry_count", 0)

        if retry_count > self.max_retries:
            return "end"
        else:
            return GraphConstants.Routes.PREPARE_CONTEXT

    def _build_graph(self):
        """
        Build the LangGraph workflow for filter generation.

        Returns:
            Configured StateGraph
        """
        # Create the graph
        workflow = StateGraph(ItemGenerationState)

        # Add nodes
        workflow.add_node(GraphConstants.Nodes.PREPARE_CONTEXT, self._prepare_context_node)
        workflow.add_node(GraphConstants.Nodes.GENERATE, self._generate_node)
        workflow.add_node(GraphConstants.Nodes.TOOLS, ToolNode(self.tools))
        workflow.add_node(GraphConstants.Nodes.VALIDATE, self._validate_node)
        workflow.add_node(GraphConstants.Nodes.CREATE, self._creation_node)
        workflow.add_node(GraphConstants.Nodes.RETRY, self._retry_node)

        # Add edges
        workflow.set_entry_point(GraphConstants.Nodes.PREPARE_CONTEXT)
        workflow.add_edge(GraphConstants.Nodes.PREPARE_CONTEXT, GraphConstants.Nodes.GENERATE)

        # Conditional routing after generation
        workflow.add_conditional_edges(
            GraphConstants.Nodes.GENERATE,
            self._route_after_generation,
            {
                GraphConstants.Routes.TOOLS: GraphConstants.Routes.TOOLS,
                GraphConstants.Routes.VALIDATE: GraphConstants.Routes.VALIDATE,
                GraphConstants.Routes.RETRY: GraphConstants.Routes.RETRY,
            },
        )

        # Tool execution flows back to generation
        workflow.add_edge(GraphConstants.Nodes.TOOLS, GraphConstants.Nodes.GENERATE)

        # Validation routing
        workflow.add_conditional_edges(
            GraphConstants.Nodes.VALIDATE,
            self._route_after_validation,
            {"create": GraphConstants.Routes.CREATE, GraphConstants.Routes.RETRY: GraphConstants.Routes.RETRY},
        )

        # Retry flows back to generation or ends
        workflow.add_conditional_edges(
            GraphConstants.Nodes.RETRY,
            self._route_after_retry,
            {GraphConstants.Routes.PREPARE_CONTEXT: GraphConstants.Routes.PREPARE_CONTEXT, "end": GraphConstants.Routes.END},
        )
        workflow.add_edge(GraphConstants.Nodes.CREATE, GraphConstants.Routes.END)

        return workflow

    def execute(
            self, query: str, values_api_url: str, store=None, context: Optional[Dict] = None
    ) -> str:
        """
        Generate filter code from natural language query using LangGraph.

        Args:
            query: Natural language query
            field_list: List of available fields
            values_api_url: URL template for field values
            context: Additional context information

        Returns:
            Generated Python code

        Raises:
            ValueError: If generation fails after retries
        """
        if store is None:
            store= {}
        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "field_list": get_field_list(self.flow_id),
            "values_api_url": values_api_url,
            "context": context,
            "generated_code": None,
            "validation_errors": [],
            "retry_count": 0,
            "tool_iteration_count": 0,
            "store": store
        }

        # Create a unique thread ID for this conversation
        config_dict = {"configurable": {"thread_id": self.thread_id}}

        try:
            # Run the graph
            print(f"invoked")
            state = self.compiled_graph.invoke(initial_state, config_dict)
            generated_code = state.get("generated_code")
            return "item successfully created"
        except Exception as e:
            print(f"LangGraph filter generation failed: {e}")
            raise ValueError(f"Filter generation failed: {e}")

    def resume(self, query):
        print("invoke resume")
        config_dict = {"configurable": {"thread_id": self.thread_id}}
        state = self.compiled_graph.invoke(Command(resume=query), config_dict)
        generated_code = state.get("generated_code")
        return generated_code

def get_compiled_graph(flow_id, memory, thread_id):
    return ItemCreationGraph(flow_id, memory, thread_id)



if __name__ == "__main__":
    from langgraph.checkpoint.mongodb import MongoDBSaver
    from pymongo import MongoClient

    MONGO_URI = "mongodb://localhost:27017/"
    DB_NAME = "checkpoints"
    client = MongoClient(MONGO_URI)
    checkpointer = MongoDBSaver(client=client, db_name=DB_NAME)
    thread_id = 33
    values_api_url = "https://localhost.tst.zingworks.com/case/2/Ac9iuLeMiQYd/Leave_Request_Board/view/Leave_Request_Board_all/field/{field_id}/values"
    obj = ItemCreationGraph("flow_id", checkpointer, thread_id)
    obj.execute("planning to take leave apply for it, from aug 8 2025 to aug 10 2025 for vacation", values_api_url)
    #obj.resume("for vacation")
    #obj.resume("from aug 8 2025 to aug 10 2025")
    #obj.resume("from aug 8 2025 to aug 10 2025 for vacation")
