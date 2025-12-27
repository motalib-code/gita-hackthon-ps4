from typing import TypedDict, List, Annotated
import operator

class ChakravyuhState(TypedDict):
    query: str
    intent: str  # "VISUAL", "TEXT", "COMPOSITE"
    retrieved_docs: List[dict] # List of nodes/dicts
    conflict_detected: bool
    conflict_reasoning: str
    final_answer: str
    retry_count: int
