import sys
import os

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.graph import build_graph

def main():
    print("🎨 Generating Agent Graph visualization...")
    
    # Initialize the graph
    app = build_graph()
    
    # Generate the Mermaid PNG data
    png_data = app.get_graph().draw_mermaid_png()
    
    # Save the image to the root of the project
    output_path = "agent_graph.png"
    with open(output_path, "wb") as f:
        f.write(png_data)
        
    print(f"✅ Graph saved successfully as '{output_path}' in your project root!")

if __name__ == "__main__":
    main()