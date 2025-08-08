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
from enum import Enum
from pydantic import BaseModel
from typing import Annotated, Sequence, List, Literal
from pydantic import BaseModel, Field
from agent_store.item_creation_agent.graph import ItemCreationGraph
from agent_store.item_update_agent.graph import ItemUpdateGraph

class ItemCrudOrchestratorState(TypedDict):
    """State definition for the filter generation graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    store: Optional[Dict]

class Supervisor(BaseModel):
    next: Literal["item_creater", "item_updater"] = Field(
        description="Determines which specialist to activate next in the workflow sequence: "
                    "'item_creater' when user want to create an item, "
                    "'item_updater' user want to update an item, "
    )

class ItemCrudOrchestrator:
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

        # Build the graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)


    def _item_creator(self, state):
        item_creation_agent = ItemCreationGraph(self.flow_id, self.memory, self.thread_id)
        values_api_url = "https://localhost.tst.zingworks.com/case/2/Ac9iuLeMiQYd/Leave_Request_Board/view/Leave_Request_Board_all/field/{field_id}/values"
        response = item_creation_agent.execute(state.get(GraphConstants.StateKeys.MESSAGES, [])[-1].content, values_api_url, state.get("store"))
        return {**state, GraphConstants.StateKeys.MESSAGES: [HumanMessage(content=response)]}

    def _item_updator(self, state):
        item_updater_agent = ItemUpdateGraph(self.flow_id, self.memory, self.thread_id)
        values_api_url = "https://localhost.tst.zingworks.com/case/2/Ac9iuLeMiQYd/Leave_Request_Board/view/Leave_Request_Board_all/field/{field_id}/values"
        response = item_updater_agent.execute(state.get(GraphConstants.StateKeys.MESSAGES, [])[-1].content,
                                               values_api_url)
        return {**state, GraphConstants.StateKeys.MESSAGES: [HumanMessage(content=response)]}


    def _orchestrator_node(self, state):
        system_prompt = ('''

                You are a workflow supervisor managing a team of two specialized agents: Item_creator, Item_updator. Your role is to orchestrate the workflow by selecting the most appropriate next agent based on the current state and needs of the task. 

                **Team Members**:
                1. **ItemCreator**: Create an item.
                2. **ItemUpdater**: Update an item.

                **Your Responsibilities**:
                1. Analyze each user request and agent response for completeness, accuracy, and relevance.
                2. Route the task to the most appropriate agent at each decision point.
                3. Maintain workflow momentum by avoiding redundant agent assignments.
                4. Continue the process until the user's request is fully and satisfactorily resolved.

                Your objective is to create an efficient workflow that leverages each agent's strengths while minimizing unnecessary steps, ultimately delivering complete and accurate solutions to user requests.

            ''')

        messages = [
                       {"role": "system", "content": system_prompt},
                   ] + state["messages"]

        response = self.llm.with_structured_output(Supervisor).invoke(messages)

        goto = response.next

        print(f"--- Workflow Transition: Supervisor → {goto.upper()} ---")

        return Command(
            goto=goto,
        )


    def _build_graph(self):
        workflow = StateGraph(ItemCrudOrchestratorState)

        # Add nodes
        workflow.add_node("speaker_selector", self._orchestrator_node)
        workflow.add_node("item_creater", self._item_creator)
        workflow.add_node("item_updater", self._item_updator)

        # Add edges
        workflow.set_entry_point("speaker_selector")
        workflow.add_edge("item_creater", GraphConstants.Routes.END)
        workflow.add_edge("item_updater", GraphConstants.Routes.END)

        return workflow

    def execute(self, query, store=None):
        if store is None:
            store= {}
        config_dict = {"configurable": {"thread_id": self.thread_id}}
        state = self.compiled_graph.invoke({GraphConstants.StateKeys.MESSAGES: [HumanMessage(content=query)], "store": store}, config_dict)
        return state.get(GraphConstants.StateKeys.MESSAGES)[-1].content

if __name__ == "__main__":
    from langgraph.checkpoint.mongodb import MongoDBSaver
    from pymongo import MongoClient

    MONGO_URI = "mongodb://localhost:27017/"
    DB_NAME = "checkpoints"
    client = MongoClient(MONGO_URI)
    checkpointer = MongoDBSaver(client=client, db_name=DB_NAME)
    thread_id = 33
    orchestrator = ItemCrudOrchestrator("flow", checkpointer, thread_id)
    orchestrator.execute("planning to take leave apply for it, from aug 8 2025 to aug 10 2025 for vacation")