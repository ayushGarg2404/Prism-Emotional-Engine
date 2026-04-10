from prism_graph import build_graph
from prism_schema import PrismResponse

def analyze_reflection(user_text: str, baseline: dict, constitution_str: str, ingestion_metadata: dict) -> PrismResponse:
    app = build_graph()
    
    initial_state = {
        "user_text": user_text,
        "baseline": baseline,
        "constitution_str": constitution_str,
        "ingestion_metadata": ingestion_metadata,
        "supervisor_rejections": 0
    }
    
    final_state = app.invoke(initial_state)
    
    audit = final_state["audit_result"]
    subtext = final_state["subtext_result"]
    mirror = final_state["therapeutic_mirror"]
    
    return PrismResponse(
        vector=audit.vector,
        audit=audit,
        subtext=subtext,
        therapeutic_mirror=mirror
    )
