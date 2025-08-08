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


class MessageType(str, Enum):
    ANSWER = "answer"
    CONTINUATION = "continuation"
    NEW_CONVERSATION = "new_conversation"


class ClassificationResult(BaseModel):
    message_type: MessageType


load_dotenv()


class FlowResumeAgent:
    def __init__(
        self,
        system_prompt: str = PromptConstants.FlowResumeAgent.SYSTEM_MESSAGE,
        model: str = "gpt-4o",
        temperature: float = 0,
        max_retries: int = 3,
        max_tool_iterations: int = 5,
    ):
        """
        Initialize the LangGraph-based flow resume agent.

        System Prompt Example:
        You are an AI assistant that determines if a new user message is a direct continuation
        of the immediately preceding AI message provided as previous.

        Your task:

        Compare the new user message only to previous (ignore any other history).

        Classify:
        CONTINUATION → the new message directly answers or follows previous.
        NEW_CONVERSATION → the new message ignores or is unrelated to previous.

        Rules:
        Only previous matters.
        If previous contains a question or instruction and the new message responds or follows it,
        classify as CONTINUATION.
        If the new message changes topic, asks something else, or skips previous,
        classify as NEW_CONVERSATION.
        """
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.max_tool_iterations = max_tool_iterations
        self.retry_from_scratch = False

        # Initialize LLM with structured output schema
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=OPEN_AI_KEY,
            temperature=self.temperature,
        ).with_structured_output(ClassificationResult)

    def execute(self, last_interrupted_message: str, new_user_message: str) -> ClassificationResult:
        """
        Classify whether the new_user_message is a continuation of last_interrupted_message.
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    f"previous: {last_interrupted_message}\n"
                    f"new message: {new_user_message}"
                )
            ),
        ]

        # Get structured classification from LLM
        response: ClassificationResult = self.llm.invoke(messages)
        return response


# Example usage:
if __name__ == "__main__":
    agent = FlowResumeAgent()
    result = agent.execute(
        last_interrupted_message="How many days and what is the reason?",
        new_user_message="why reason",
    )
    print(result.json())
