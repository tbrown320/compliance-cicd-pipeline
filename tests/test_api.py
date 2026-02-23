import pytest
import json
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"


def test_create_transaction(client):
    """Test creating a compliance transaction"""
    transaction = {
        "transaction_id": "TXN001",
        "amount": 1000.00,
        "timestamp": "2025-01-29T10:00:00",
        "status": "compliant",
    }
    response = client.post(
        "/api/compliance/transactions",
        data=json.dumps(transaction),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["id"] == "TXN001"


def test_create_transaction_invalid_data(client):
    """Test validation of invalid transaction data"""
    invalid_transaction = {
        "transaction_id": "TXN002",
        "amount": 500.00,
        # Missing 'timestamp' and 'status' fields!
    }
    response = client.post(
        "/api/compliance/transactions",
        data=json.dumps(invalid_transaction),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_get_transaction(client):
    """Test retrieving a transaction"""
    # First, create a transaction
    transaction = {
        "transaction_id": "TXN003",
        "amount": 2000.00,
        "timestamp": "2025-01-29T11:00:00",
        "status": "compliant",
    }
    client.post(
        "/api/compliance/transactions",
        data=json.dumps(transaction),
        content_type="application/json",
    )

    # Now retrieve it
    response = client.get("/api/compliance/transactions/TXN003")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["transaction_id"] == "TXN003"
    assert data["amount"] == 2000.00


def test_list_transactions(client):
    """Test listing all transactions"""
    response = client.get("/api/compliance/transactions")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "count" in data
    assert "transactions" in data


def test_compliance_report(client):
    """Test compliance report generation"""
    response = client.get("/api/compliance/report")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total_transactions" in data
    assert "compliance_rate" in data
    assert "status_breakdown" in data


def test_transaction_not_found(client):
    """Test retrieving non-existent transaction"""
    response = client.get("/api/compliance/transactions/NONEXISTENT")
    assert response.status_code == 404


def test_delete_transaction(client):
    """test deleting a transaction"""
    transaction = {
        "transaction_id": "TX005",
        "amount": 2500.00,
        "timestamp": "2025-02-27T11:00:00",
        "status": "compliant",
    }
    client.post(
        "/api/compliance/transactions",
        data=json.dumps(transaction),
        content_type="application/json",
    )
    response = client.get("/api/compliance/transactions/TX005")
    assert response.status_code == 200

    response = client.delete("/api/compliance/transactions/TX005")
    assert response.status_code == 200

    response = client.get("/api/compliance/transactions/TX005")
    assert response.status_code == 404
