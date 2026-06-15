from typing import TypedDict, List, Dict, Any

class FeedbackState(TypedDict):
    current_batch: List[Dict[str, Any]]
    processed_items: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    errors: List[Dict[str, Any]]
