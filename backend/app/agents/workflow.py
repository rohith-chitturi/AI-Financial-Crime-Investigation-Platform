from langgraph.graph import StateGraph, END
from app.agents.state import InvestigationState
from app.agents.nodes import (
    coordinator_node,
    TransactionIntelNode,
    AMLInvestigatorNode,
    KnowledgeGraphNode,
    CustomerRiskNode,
    regulatory_node,
    ReasoningNode,
    RecommendationNode,
    ReportGeneratorNode
)

def create_investigation_workflow():
    """
    Builds and compiles the Multi-Agent Investigation StateGraph.
    """
    workflow = StateGraph(InvestigationState)
    
    # Instantiate Nodes
    transaction_node = TransactionIntelNode()
    aml_node = AMLInvestigatorNode()
    graph_node = KnowledgeGraphNode()
    customer_node = CustomerRiskNode()
    reasoning_node = ReasoningNode()
    recommendation_node = RecommendationNode()
    report_node = ReportGeneratorNode()
    
    # Add Nodes
    workflow.add_node("Coordinator", coordinator_node)
    workflow.add_node("TransactionIntel", transaction_node)
    workflow.add_node("AMLInvestigator", aml_node)
    workflow.add_node("KnowledgeGraph", graph_node)
    workflow.add_node("CustomerRisk", customer_node)
    workflow.add_node("Regulatory", regulatory_node)
    workflow.add_node("Reasoning", reasoning_node)
    workflow.add_node("Recommendation", recommendation_node)
    workflow.add_node("ReportGenerator", report_node)
    
    # Define Edges
    workflow.set_entry_point("Coordinator")
    
    workflow.add_edge("Coordinator", "TransactionIntel")
    workflow.add_edge("TransactionIntel", "AMLInvestigator")
    workflow.add_edge("AMLInvestigator", "KnowledgeGraph")
    workflow.add_edge("KnowledgeGraph", "CustomerRisk")
    workflow.add_edge("CustomerRisk", "Regulatory")
    workflow.add_edge("Regulatory", "Reasoning")
    workflow.add_edge("Reasoning", "Recommendation")
    workflow.add_edge("Recommendation", "ReportGenerator")
    workflow.add_edge("ReportGenerator", END)
    
    # Compile
    return workflow.compile()

# Provide a compiled singleton
investigation_graph = create_investigation_workflow()
