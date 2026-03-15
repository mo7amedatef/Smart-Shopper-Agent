import sys
import os

# Go up 3 levels to reach the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

import chainlit as cl
import uuid
from langchain_core.messages import HumanMessage
from loguru import logger

# Import our compiled LangGraph agent
from src.agent.graph import build_graph

@cl.on_chat_start
async def on_chat_start():
    """Initializes the agent session."""
    logger.info("New chat session started in UI.")
    
    agent_app = build_graph()
    cl.user_session.set("agent_app", agent_app)
    
    thread_id = str(uuid.uuid4())
    cl.user_session.set("config", {"configurable": {"thread_id": thread_id}})
    
    await cl.Message(
        content="Welcome to Egy-Shop! 🛒 I'm your smart shopping assistant. What are you looking to buy today?",
        author="Assistant"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handles incoming messages with Token-by-Token streaming and Tool state handling."""
    agent_app = cl.user_session.get("agent_app")
    config = cl.user_session.get("config")
    
    state_input = {"messages": [HumanMessage(content=message.content)]}
    
    # Create an empty message for the AI response
    ui_msg = cl.Message(content="", author="Assistant")
    await ui_msg.send()
    
    tool_msg = None
    
    try:
        # Using astream_events for granular control (Token-by-Token)
        async for event in agent_app.astream_events(state_input, config=config, version="v2"):
            kind = event["event"]
            
            # 1. STREAMING TOKEN BY TOKEN ✨
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # Append each token dynamically to the UI
                if chunk.content and isinstance(chunk.content, str):
                    await ui_msg.stream_token(chunk.content)
            
            # 2. TOOL STARTED ⏳
            elif kind == "on_tool_start":
                tool_name = event["name"]
                if tool_name == "search_ecommerce_sites":
                    tool_msg = cl.Message(
                        content="⏳ **Searching Amazon, B.TECH, and Noon live... Please wait a few seconds!**", 
                        author="System"
                    )
                    await tool_msg.send()
                    
            # 3. TOOL FINISHED ✅
            elif kind == "on_tool_end":
                if tool_msg:
                    await tool_msg.remove()
                    tool_msg = None
        
        # Finalize the streaming message
        await ui_msg.update()
        
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        if tool_msg:
            await tool_msg.remove()
        await cl.Message(content=f"⚠️ System encountered an issue: {str(e)}", author="System").send()