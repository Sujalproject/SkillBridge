
from langgraph.graph import END, START, StateGraph

from backend.graphs.nodes import (
    extract_resume_node,
    analyze_resume_node,
    analyze_skill_gap_node,
)
from backend.graphs.state import CareerState


def build_career_graph():
    """Build and compile the SkillBridge career-analysis graph."""
    graph = StateGraph(CareerState)
    
    graph.add_node("extract_resume", extract_resume_node)
    graph.add_node("analyze_resume", analyze_resume_node)
    graph.add_node("analyze_skill_gap", analyze_skill_gap_node)

    graph.add_edge(START, "extract_resume")
    graph.add_edge("extract_resume", "analyze_resume")
    graph.add_edge("analyze_resume", "analyze_skill_gap")
    graph.add_edge("analyze_skill_gap", END)

    return graph.compile()


career_graph = build_career_graph()
