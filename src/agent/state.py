from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # These messages will delete the entire chat history between the user and the LLM.
    # The add_messages option ensures that new messages are added to the old ones, not deleted.
    messages: Annotated[list, add_messages]
    
    # The flag that the LLM will change when it has collected enough data to start a search
    ready_to_search: bool
    
    # The keyword that the LLM will infer and send to the Scrapers
    search_query: str
    
    # The budget that the user will specify and we will store here
    budget: float