from typing import Dict, Any, List
from datetime import datetime
from prism_schema import IngestionMetadata

class PrismIngestion:
    def __init__(self):
        pass
        
    def process_entry(self, user_id: str, text: str, timestamp_str: str, baseline_meta: Dict[str, Any]) -> IngestionMetadata:
        """
        Process a long-form journal entry calculating inter-entry gaps 
        based on the user's historical baseline.
        """
        current_time = datetime.fromisoformat(timestamp_str)
        
        # Calculate inter-entry gap
        inter_entry_gap_days = 0.0
        last_entry_str = baseline_meta.get("last_entry_timestamp")
        if last_entry_str:
            last_entry_time = datetime.fromisoformat(last_entry_str)
            delta = current_time - last_entry_time
            inter_entry_gap_days = max(0.0, delta.total_seconds() / 86400.0)
            
        return IngestionMetadata(
            inter_entry_gap_days=round(inter_entry_gap_days, 2),
            audio_array=[],
            visual_array=[]
        )
