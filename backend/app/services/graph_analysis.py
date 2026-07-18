import logging
from neo4j import AsyncSession as Neo4jAsyncSession
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GraphAnalysisService:
    """
    Analyzes transaction patterns in Neo4j to detect financial crimes.
    """
    
    @staticmethod
    async def analyze_account_risk(neo4j_session: Neo4jAsyncSession, account_id: str) -> Dict[str, Any]:
        """
        Calculates graph risk indicators for an account.
        """
        score = 0.0
        explanations: List[str] = []
        
        # 1. Circular Fund Movement Detection (3 to 5 hops returning to same account)
        # We look for a path where account transfers to another, which transfers to another... and comes back.
        # Ensure time constraints theoretically (we simplify here by just path topology).
        circular_query = """
        MATCH path = (a:Account {id: $account_id})-[:TRANSFERRED_TO*3..5]->(a)
        RETURN nodes(path) AS cycle_nodes, relationships(path) AS cycle_rels
        LIMIT 5
        """
        result = await neo4j_session.run(circular_query, account_id=account_id)
        records = await result.data()
        
        if records:
            score += 40.0
            explanations.append(f"Detected circular money movement involving {len(records[0]['cycle_nodes']) - 1} hops.")

        # 2. Mule Fan-in / Fan-out
        # Fan-in: Receives transfers from many distinct accounts.
        # Fan-out: Sends transfers to many distinct accounts.
        # A classic mule pattern receives from many and sends to one/few, or receives from one/few and sends to many.
        mule_query = """
        MATCH (a:Account {id: $account_id})
        OPTIONAL MATCH (src:Account)-[:TRANSFERRED_TO]->(a)
        WITH a, count(DISTINCT src) AS in_degree
        OPTIONAL MATCH (a)-[:TRANSFERRED_TO]->(dst:Account)
        WITH a, in_degree, count(DISTINCT dst) AS out_degree
        RETURN in_degree, out_degree
        """
        result = await neo4j_session.run(mule_query, account_id=account_id)
        mule_record = await result.single()
        
        if mule_record:
            in_degree = mule_record["in_degree"]
            out_degree = mule_record["out_degree"]
            
            if in_degree > 5 and out_degree <= 2:
                score += 30.0
                explanations.append(f"Mule Fan-In detected: Received transfers from {in_degree} unique accounts, sent to {out_degree}.")
            elif in_degree <= 2 and out_degree > 5:
                score += 30.0
                explanations.append(f"Mule Fan-Out detected: Received transfers from {in_degree} accounts, sent to {out_degree} unique accounts.")
            elif in_degree > 3 and out_degree > 3:
                score += 20.0
                explanations.append(f"High-degree transaction hub: Interacting with {in_degree} senders and {out_degree} receivers.")

        # 3. Connection to High-Risk Cluster / Organization
        # E.g. interacting with an account that is associated with a risky organization or many other accounts.
        cluster_query = """
        MATCH (a:Account {id: $account_id})-[:TRANSFERRED_TO]-(other:Account)-[:ASSOCIATED_WITH]->(o:Organization)
        RETURN count(DISTINCT o) AS linked_orgs
        """
        result = await neo4j_session.run(cluster_query, account_id=account_id)
        cluster_record = await result.single()
        if cluster_record and cluster_record["linked_orgs"] > 0:
            orgs_count = cluster_record["linked_orgs"]
            score += 10.0
            explanations.append(f"Linked to {orgs_count} external organizations indirectly via transfers.")

        # Normalize score
        score = min(score, 100.0)
        
        return {
            "graph_score": score,
            "graph_evidence": explanations,
            "graph_version": "1.0.0"
        }

    @staticmethod
    async def analyze_transaction_risk(neo4j_session: Neo4jAsyncSession, source_account_id: str, destination_account_id: str = None) -> Dict[str, Any]:
        """
        Analyze risk context specific to a transaction using graph topology.
        If it's an internal transfer, check pathing.
        """
        risk_data = await GraphAnalysisService.analyze_account_risk(neo4j_session, source_account_id)
        
        # If there's a destination, check if they share a common customer, or have dense cyclic paths
        if destination_account_id:
            shared_org_query = """
            MATCH (src:Account {id: $src_id})-[:ASSOCIATED_WITH]->(o:Organization)<-[:ASSOCIATED_WITH]-(dst:Account {id: $dst_id})
            RETURN o.name AS org_name
            """
            result = await neo4j_session.run(shared_org_query, src_id=source_account_id, dst_id=destination_account_id)
            records = await result.data()
            if records:
                # Transacting within the same organization
                pass # Can be normal or risky depending on context. Let's not penalize heavily, maybe just note it.
                risk_data["graph_evidence"].append(f"Transaction between accounts in the same organization: {records[0]['org_name']}")

        return risk_data
