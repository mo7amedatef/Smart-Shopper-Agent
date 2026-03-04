import sys
import os
import asyncio

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.agent.graph import build_graph

async def main():
    print("🤖 Agent is waking up... (Type 'quit' or 'exit' to stop)")
    
    # Initialize the graph
    agent_app = build_graph()
    
    config = {"configurable": {"thread_id": "user_session_1"}}
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("🤖 Agent: Goodbye!")
            break
            
        state_input = {"messages": [HumanMessage(content=user_input)]}
        
        # We changed stream() to astream() and added 'async for'
        async for event in agent_app.astream(state_input, config=config):
            for value in event.values():
                print("\n🤖 Agent:", value["messages"][-1].content)

if __name__ == "__main__":
    # Run the main function in an asyncio event loop
    asyncio.run(main())