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


class FlowPickerAgent:
    def __init__(
        self,
        system_prompt: str = PromptConstants.FlowResumeAgent.SYSTEM_MESSAGE,
        model: str = "gpt-4o",
        temperature: float = 0,
        max_retries: int = 3,
        max_tool_iterations: int = 5,
    ):

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

    def execute(self,  new_user_message: str) -> ClassificationResult:
        """
        Classify whether the new_user_message is a continuation of last_interrupted_message.
        """
        return "Leave management"
