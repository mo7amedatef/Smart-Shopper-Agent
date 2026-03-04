import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from src.agent.state import AgentState

# Load environment variables (for GROQ_API_KEY)
load_dotenv()

# Initialize Groq with Llama 3 (8B is blazing fast and smart enough for this)
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.3
)

# The Persona and Instructions for the LLM
SYSTEM_PROMPT = """You are a smart, friendly, and expert personal shopping assistant for the Egyptian market. 
Your goal is to help the user find the perfect product to buy (e.g., laptops, phones, electronics).

Follow these rules strictly:
1. Greet the user and naturally ask what they are looking to buy today.
2. Ask clarifying questions one by one to understand their needs (e.g., budget in EGP, main usage, preferred brand).
3. Do NOT make up product prices or specifications.
4. Keep the conversation engaging but concise.
5. For now, just converse with the user and gather requirements. (Tool calling will be enabled later).
"""

def chat_node(state: AgentState):
    """
    Handles the conversation with the user and updates the chat history.
    """
    logger.info("[Agent] Thinking...")
    messages = state.get("messages", [])
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
    
    response = llm.invoke(messages)
    
    return {"messages": [response]}

def build_graph():
    """
    Builds and compiles the LangGraph workflow.
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("chat", chat_node)
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)
    
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app