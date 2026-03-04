import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from loguru import logger

from src.agent.state import AgentState
from src.agent.tools import search_ecommerce_sites

# Load environment variables (for GROQ_API_KEY)
load_dotenv()

# Initialize Groq with Llama-3.3-70B
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.3
)

# 1. BIND TOOLS TO THE LLM
# This tells the LLM: "Hey, you have these tools available if you need them."
tools = [search_ecommerce_sites]
llm_with_tools = llm.bind_tools(tools)

# Updated Persona: Now we explicitly tell it to USE the tool when ready.
# Updated Persona: Now with strict rules for the search query format!
SYSTEM_PROMPT = """You are a smart, friendly, and expert personal shopping assistant for the Egyptian market. 
Your goal is to help the user find the perfect product to buy.

Follow these rules strictly:
1. Greet the user and naturally ask what they are looking to buy today.
2. Ask clarifying questions one by one to understand their needs (budget in EGP, main usage, preferred specs/brand).
3. Do NOT make up product prices or specifications.
4. Keep the conversation engaging but concise.
5. CRITICAL: Once you have gathered enough information, YOU MUST call the `search_ecommerce_sites` tool.
6. VERY IMPORTANT: The `query` argument for the tool MUST BE short, keyword-only, and highly optimized for traditional e-commerce search engines (e.g., "Lenovo Thinkpad", "iPhone 15 Pro", "MacBook Air M1"). NEVER include conversational words like "for programming", "cheap", or "good for gaming" in the query.
"""

async def chat_node(state: AgentState):
    """
    Handles the conversation and decides whether to talk to the user or call a tool.
    """
    logger.info("[Agent] Thinking...")
    messages = state.get("messages", [])
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
    
    # We changed this to await and ainvoke to support the async tool
    response = await llm_with_tools.ainvoke(messages)
    
    return {"messages": [response]}

def build_graph():
    """
    Builds the Agentic Workflow with Tool routing.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    
    # 2. Add the Prebuilt Tool Node
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)
    
    # Define edges (Routing logic)
    workflow.set_entry_point("chat")
    
    # 3. Conditional Edge: 
    # If the LLM output has tool_calls, it goes to "tools" node.
    # If it's just text, it goes to END (waiting for user reply).
    workflow.add_conditional_edges("chat", tools_condition)
    
    # After the tool finishes running, return to the chat node so the LLM can read the results
    workflow.add_edge("tools", "chat")
    
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app