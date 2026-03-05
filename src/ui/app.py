import sys
import os
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
    """
    Initializes the agent session when a user opens the chat.
    """
    logger.info("New chat session started in UI.")
    
    # Initialize the LangGraph app
    agent_app = build_graph()
    cl.user_session.set("agent_app", agent_app)
    
    # Create a unique thread ID for memory persistence per user session
    thread_id = str(uuid.uuid4())
    cl.user_session.set("config", {"configurable": {"thread_id": thread_id}})
    
    # Send a welcoming message
    await cl.Message(
        content="Welcome to Egy-Shop! 🛒 I'm your smart shopping assistant. What are you looking to buy today?",
        author="Assistant"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handles incoming messages and streams the Agent's response.
    """
    agent_app = cl.user_session.get("agent_app")
    config = cl.user_session.get("config")
    
    state_input = {"messages": [HumanMessage(content=message.content)]}
    
    # Create an empty message for the final LLM response
    ui_msg = cl.Message(content="", author="Assistant")
    await ui_msg.send()
    
    tool_msg = None 
    
    # Stream events from LangGraph
    async for event in agent_app.astream(state_input, config=config):
        for node_name, value in event.items():
            
            if node_name == "chat":
                last_msg = value["messages"][-1]
                
                # Check if the LLM decided to use a tool!
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    tool_msg = cl.Message(
                        content="⏳ **Searching Amazon, B.TECH, and Noon live... Please wait a few seconds!**", 
                        author="System"
                    )
                    await tool_msg.send()
                    
                # If it's a normal text response to the user
                elif last_msg.content:
                  
                    if tool_msg:
                        await tool_msg.remove()
                        tool_msg = None
                        
                    ui_msg.content = last_msg.content
                    await ui_msg.update()