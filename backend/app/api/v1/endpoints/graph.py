from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jAsyncSession
from typing import Any, Dict

from app.db.database import get_db
from app.db.neo4j_database import get_neo4j_session
from app.api.dependencies import get_current_active_user
from app.db.models.user import User
from app.services.graph_sync import GraphSyncService

router = APIRouter()

@router.post("/sync")
async def sync_database_to_graph(
    db: AsyncSession = Depends(get_db),
    neo4j_session: Neo4jAsyncSession = Depends(get_neo4j_session),
    # current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Synchronizes the PostgreSQL relational data into the Neo4j Knowledge Graph.
    This performs a full sync of Customers, Organizations, Merchants, Accounts, and Transactions.
    """
    try:
        await GraphSyncService.full_sync(db, neo4j_session)
        return {"message": "Graph synchronization completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync graph: {str(e)}")

@router.get("/account/{account_id}/network")
async def get_account_network(
    account_id: str,
    depth: int = 2,
    neo4j_session: Neo4jAsyncSession = Depends(get_neo4j_session),
    # current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieves the local subgraph around an account up to a certain depth for visualization.
    """
    if depth > 4:
        raise HTTPException(status_code=400, detail="Maximum traversal depth is 4 to prevent performance issues.")
        
    query = """
    MATCH path = (a:Account {id: $account_id})-[*1..%d]-(other)
    RETURN nodes(path) AS nodes, relationships(path) AS rels
    LIMIT 100
    """ % depth
    
    result = await neo4j_session.run(query, account_id=account_id)
    records = await result.data()
    
    # We must format this as Nodes and Relationships for the frontend
    nodes_map = {}
    rels_map = {}
    
    for record in records:
        for node in record["nodes"]:
            # node is a neo4j Node object, extract labels and properties
            node_id = str(node.element_id)
            if node_id not in nodes_map:
                nodes_map[node_id] = {
                    "id": node_id,
                    "labels": list(node.labels),
                    "properties": dict(node.items())
                }
        for rel in record["rels"]:
            rel_id = str(rel.element_id)
            if rel_id not in rels_map:
                rels_map[rel_id] = {
                    "id": rel_id,
                    "type": rel.type,
                    "start_node": str(rel.start_node.element_id),
                    "end_node": str(rel.end_node.element_id),
                    "properties": dict(rel.items())
                }
                
    return {
        "nodes": list(nodes_map.values()),
        "relationships": list(rels_map.values())
    }

@router.get("/customer/{customer_id}/network")
async def get_customer_network(
    customer_id: str,
    depth: int = 2,
    neo4j_session: Neo4jAsyncSession = Depends(get_neo4j_session),
    # current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieves the local subgraph around a customer up to a certain depth for visualization.
    """
    if depth > 4:
        raise HTTPException(status_code=400, detail="Maximum traversal depth is 4 to prevent performance issues.")
        
    query = """
    MATCH path = (c:Customer {id: $customer_id})-[*1..%d]-(other)
    RETURN nodes(path) AS nodes, relationships(path) AS rels
    LIMIT 100
    """ % depth
    
    result = await neo4j_session.run(query, customer_id=customer_id)
    records = await result.data()
    
    nodes_map = {}
    rels_map = {}
    
    for record in records:
        for node in record["nodes"]:
            node_id = str(node.element_id)
            if node_id not in nodes_map:
                nodes_map[node_id] = {
                    "id": node_id,
                    "labels": list(node.labels),
                    "properties": dict(node.items())
                }
        for rel in record["rels"]:
            rel_id = str(rel.element_id)
            if rel_id not in rels_map:
                rels_map[rel_id] = {
                    "id": rel_id,
                    "type": rel.type,
                    "start_node": str(rel.start_node.element_id),
                    "end_node": str(rel.end_node.element_id),
                    "properties": dict(rel.items())
                }
                
    return {
        "nodes": list(nodes_map.values()),
        "relationships": list(rels_map.values())
    }
