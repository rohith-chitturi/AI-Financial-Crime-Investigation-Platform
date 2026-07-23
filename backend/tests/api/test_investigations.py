import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
import uuid

@pytest.fixture
def mock_llm():
    with patch('langchain_google_genai.ChatGoogleGenerativeAI.invoke') as mock_invoke:
        
        def fake_invoke(messages):
            # Try to return a JSON string if the prompt seems to be reasoning/recommendation
            prompt_content = messages[0].content
            if "Reasoning Agent" in prompt_content:
                return AIMessage(content='{"overall_assessment": "Test", "evidence_summary": "Test evidence", "confidence_explanation": "Test", "confidence_score": 85.0}')
            elif "Recommendation Agent" in prompt_content:
                return AIMessage(content='{"recommendations": ["Test Recommendation 1", "Test Recommendation 2"]}')
            else:
                return AIMessage(content="Mocked LLM Response")

        mock_invoke.side_effect = fake_invoke
        yield mock_invoke

@pytest.mark.asyncio
async def test_trigger_manual_investigation(async_client: AsyncClient, mock_llm, db_session):
    from app.main import app
    from app.api.dependencies import get_current_active_user
    from app.db.models.user import User

    # Mock Auth
    app.dependency_overrides[get_current_active_user] = lambda: User(id=uuid.uuid4(), email="test@test.com", is_active=True)
    auth_headers = {}

    # Setup test customer, account, transaction and risk analysis
    from app.db.models.customer import Customer
    from app.db.models.account import Account
    from app.db.models.transaction import Transaction
    from app.db.models.risk_analysis import TransactionRiskAnalysis
    import uuid
    
    from datetime import date
    test_customer = Customer(
        id=uuid.uuid4(),
        first_name="Test",
        last_name="User",
        email=f"testuser_{uuid.uuid4()}@example.com",
        date_of_birth=date(1990, 1, 1),
        country="US"
    )
    db_session.add(test_customer)

    test_account = Account(
        id=uuid.uuid4(),
        customer_id=test_customer.id,
        account_number=f"{uuid.uuid4().int}"[:12],
        account_type="CHECKING"
    )
    db_session.add(test_account)

    test_transaction = Transaction(
        id=uuid.uuid4(),
        source_account_id=test_account.id,
        amount=100.0,
        transaction_type="transfer"
    )
    db_session.add(test_transaction)
    
    test_risk = TransactionRiskAnalysis(
        transaction_id=test_transaction.id,
        unified_risk_score=80.0,
        ml_score=85.0,
        aml_rule_score=70.0,
        customer_risk_score=60.0,
        graph_score=90.0,
        model_version="test-v1",
        risk_level="HIGH",
        explanation="Test Explanation"
    )
    db_session.add(test_risk)
    await db_session.commit()
    await db_session.refresh(test_transaction)

    # Trigger the investigation (this will run the background task)
    response = await async_client.post(f"/api/v1/investigations/run/{test_transaction.id}", headers=auth_headers)
    assert response.status_code == 202
    assert response.json()["message"] == "Investigation triggered successfully."

    # Give it a tiny bit of time for the background task to theoretically run in a real environment
    # In pytest with FastAPI TestClient, background tasks are executed after the response is returned.
    # However, since run_investigation_task creates its own session and is async, it might need some time.
    import asyncio
    await asyncio.sleep(1)

    # Check if investigation was created
    list_response = await async_client.get("/api/v1/investigations/", headers=auth_headers)
    assert list_response.status_code == 200
    investigations = list_response.json()
    assert len(investigations) > 0
    
    inv = investigations[0]
    assert inv["transaction_id"] == str(test_transaction.id)
    assert inv["trigger_source"] == "MANUAL"
    
    # Get specific investigation
    detail_response = await async_client.get(f"/api/v1/investigations/{inv['id']}", headers=auth_headers)
    assert detail_response.status_code == 200
    inv_detail = detail_response.json()
    
    # Verify LangGraph executions were logged
    assert len(inv_detail["agent_executions"]) > 0
    if inv_detail["errors"]:
        print("ERRORS:", inv_detail["errors"])
    # The report generator should have mocked output
    assert inv_detail["report_markdown"] == "Mocked LLM Response"
