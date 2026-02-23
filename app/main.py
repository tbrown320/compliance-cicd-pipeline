from flask import Flask, request, jsonify
from functools import wraps
import logging
from datetime import datetime
import json
import os

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("audit.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

compliance_data = {}


def audit_log(func):
    """Decorator to log all API access for compliance"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(
            f"API Call: {func.__name__} | User: {request.remote_addr} | Time: {datetime.now()}"
        )
        result = func(*args, **kwargs)
        logger.info(f"API Response: {func.__name__} | Status: Success")
        return result

    return wrapper


def validate_compliance_data(data):
    """Validate incoming compliance data"""
    required_fields = ["transaction_id", "amount", "timestamp", "status"]
    return all(field in data for field in required_fields)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for load balancer"""
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": os.getenv("APP_VERSION", "1.0.0"),
            }
        ),
        200,
    )


@app.route("/api/compliance/transactions", methods=["POST"])
@audit_log
def create_transaction():
    """Create new compliance transaction record"""
    data = request.get_json()

    if not validate_compliance_data(data):
        logger.warning(f"Invalid data submission from {request.remote_addr}")
        return jsonify({"error": "Invalid data format"}), 400

    transaction_id = data["transaction_id"]
    compliance_data[transaction_id] = {
        **data,
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
    }

    logger.info(f"Transaction created: {transaction_id}")
    return jsonify({"message": "Transaction created", "id": transaction_id}), 201


@app.route("/api/compliance/transactions/<transaction_id>", methods=["GET"])
@audit_log
def get_transaction(transaction_id):
    """Retrieve compliance transaction record"""
    if transaction_id not in compliance_data:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify(compliance_data[transaction_id]), 200


@app.route("/api/compliance/transactions", methods=["GET"])
@audit_log
def list_transactions():
    """List all compliance transactions"""
    return (
        jsonify(
            {
                "count": len(compliance_data),
                "transactions": list(compliance_data.values()),
            }
        ),
        200,
    )


@app.route("/api/compliance/transactions/<transaction_id>", methods=["DELETE"])
@audit_log
def delete_transaction(transaction_id):
    """Deletes a transaction from the database"""
    if transaction_id in compliance_data:
        del compliance_data[transaction_id]
        return jsonify({"message": "Transaction deleted"}), 200
    if transaction_id not in compliance_data:
        return jsonify({"error": "Transaction not found"}), 404


@app.route("/api/compliance/report", methods=["GET"])
@audit_log
def compliance_report():
    """Generate compliance summary report"""
    total_transactions = len(compliance_data)
    status_breakdown = {}

    for transaction in compliance_data.values():
        status = transaction.get("status", "unknown")
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

    report = {
        "report_date": datetime.now().isoformat(),
        "total_transactions": total_transactions,
        "status_breakdown": status_breakdown,
        "compliance_rate": status_breakdown.get("compliant", 0)
        / max(total_transactions, 1)
        * 100,
    }

    logger.info("Compliance report generated")
    return jsonify(report), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
