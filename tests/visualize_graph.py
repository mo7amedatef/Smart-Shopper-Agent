import sys
import os

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.graph import build_graph

def main():
    print("🎨 Generating Agent Architecture Graph...")
    
    # 1. Build the graph
    agent_app = build_graph()
    
    # 2. Extract the graph and convert it to a PNG image using Mermaid
    try:
        graph_png_bytes = agent_app.get_graph().draw_mermaid_png()
        
        # 3. Save the image to the project root
        output_path = "agent_architecture.png"
        with open(output_path, "wb") as f:
            f.write(graph_png_bytes)
            
        print(f"Success! Open the file '{output_path}' in your project folder to see the magic.")
    except Exception as e:
        print(f"Error generating image: {e}")
        print("\nHere is the ASCII version instead:\n")
        print(agent_app.get_graph().draw_ascii())

if __name__ == "__main__":
    main()