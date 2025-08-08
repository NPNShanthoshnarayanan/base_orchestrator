from agent_store.flow_resume_agent.graph import FlowResumeAgent
from agent_store.item_creation_agent.graph import get_compiled_graph as create_get_compiled_graph
from agent_store.item_update_agent.graph import get_compiled_graph as update_get_compiled_graph
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

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

from agent_store.flow_picker_agent.graph import FlowPickerAgent
from agent_store.item_crud_orchestrator.graph import ItemCrudOrchestrator

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "checkpoints"
client = MongoClient(MONGO_URI)
checkpointer = MongoDBSaver(client=client, db_name=DB_NAME)
thread_id = 33


class OrchestratorState(TypedDict):
    """State definition for the filter generation graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    store: Optional[Dict]

class MainOrchestrator:
    def __init__(self, query):
        self.query = query
        self.interrupted_message = None
        self.subgraph_id = None
        self.memory = MongoDBSaver(client=client, db_name=DB_NAME)
        self.thread_id = 48
        self.subgraph_config = {"item_creater_agent": lambda flow_id, memory, thread_id: create_get_compiled_graph(flow_id, memory, thread_id),
                                "item_updator_agent": lambda flow_id, memory, thread_id: update_get_compiled_graph(flow_id, memory, thread_id)}
        self.flow_id = None
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)

    def _collect_interrupted_message(self, state):
        store = state.get("store", {})
        print(f"store-> {store}")
        if "interrupted_message" in store:
            self.interrupted_message = store.get("interrupted_message")
            self.subgraph_id = store.get("subgraph_id")
        return {**state}

    def _flow_resume_node(self, state):
        if self.interrupted_message:
            flow_resume_agent = FlowResumeAgent()
            result = flow_resume_agent.execute(self.interrupted_message, self.query)
            if result == "answer":
                self.subgraph_config[self.subgraph_id]("flow_id", self.memory, self.thread_id).resume(self.query)
                return Command(goto=GraphConstants.Routes.END)
            return {**state}

    def _flow_picker_node(self, state):
       self.flow_id = FlowPickerAgent().execute(self.query)
       return {**state}

    def _item_crud_orchestrator(self, state):
        response = ItemCrudOrchestrator(self.flow_id, self.memory, self.thread_id).execute(self.query, state.get("store"))
        return {**state, GraphConstants.StateKeys.MESSAGES: [HumanMessage(content=response)]}



    def _build_graph(self):
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("collect_interruoted_message", self._collect_interrupted_message)
        workflow.add_node("flow_resume", self._flow_resume_node)
        workflow.add_node("flow_picker", self._flow_picker_node)
        workflow.add_node("item_crud_orchestrator", self._item_crud_orchestrator)

        # Add edges
        workflow.set_entry_point("collect_interruoted_message")
        workflow.add_edge("collect_interruoted_message", "flow_resume")
        workflow.add_edge("flow_resume", "flow_picker")
        workflow.add_edge("flow_picker", "item_crud_orchestrator")
        workflow.add_edge("item_crud_orchestrator", GraphConstants.Routes.END)

        return workflow

    def execute(self):
        config_dict = {"configurable": {"thread_id": self.thread_id}}
        state = self.compiled_graph.get_state(config_dict)
        print(state)
        return self.compiled_graph.invoke({GraphConstants.StateKeys.MESSAGES: [HumanMessage(content=self.query)], "store": {}} if not state else state, config_dict)


if __name__ == "__main__":
    # "planning to take leave apply for it, from aug 8 2025 to aug 10 2025 for vacation"
    obj = MainOrchestrator("from aug 8 2025 to aug 10 2025 for vacation")
    print(obj.execute())
