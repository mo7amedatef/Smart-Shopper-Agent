import sys
import os

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.agent.graph import build_graph

def main():
    print("🤖 Agent is waking up... (Type 'quit' or 'exit' to stop)")
    
    # Initialize the graph
    agent_app = build_graph()
    
    # We need a unique thread ID to keep the memory of this specific conversation
    config = {"configurable": {"thread_id": "user_session_1"}}
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("🤖 Agent: Goodbye!")
            break
            
        # Format the user input
        state_input = {"messages": [HumanMessage(content=user_input)]}
        
        # Stream the response from the graph
        for event in agent_app.stream(state_input, config=config):
            for value in event.values():
                print("\n🤖 Agent:", value["messages"][-1].content)

if __name__ == "__main__":
    main()