from typing import Dict, Any, Optional

DEFAULT_COST_CONFIG = {
    "token_cost_rate": 0.00001,         # $10 per million tokens
    "agent_call_cost_rate": 0.005,      # $5 per 1,000 calls
    "premium_model_cost_rate": 0.05,    # $50 per 1,000 premium calls
    "compute_second_cost_rate": 0.0005,  # $1.80 per hour of compute
    "document_cost_rate": 0.002         # $2 per 1,000 documents
}

def calculate_monthly_bill(
    tasks: int,
    base_price: float,
    included_units: int,
    overage_price: float
) -> float:
    """
    Deterministic calculation of a customer's monthly bill.
    Bill = base_price + max(0, tasks - included_units) * overage_price
    """
    if tasks <= included_units:
        return float(base_price)
    
    overage_tasks = tasks - included_units
    total_bill = base_price + (overage_tasks * overage_price)
    return float(round(total_bill, 2))

def calculate_infra_cost(
    tokens_used: int,
    agent_calls: int,
    premium_model_calls: int,
    compute_seconds: int,
    documents_processed: int,
    cost_config: Optional[Dict[str, float]] = None
) -> float:
    """
    Deterministic calculation of the estimated infrastructure cost.
    """
    config = cost_config or DEFAULT_COST_CONFIG
    
    token_cost = tokens_used * config["token_cost_rate"]
    agent_cost = agent_calls * config["agent_call_cost_rate"]
    premium_cost = premium_model_calls * config["premium_model_cost_rate"]
    compute_cost = compute_seconds * config["compute_second_cost_rate"]
    doc_cost = documents_processed * config["document_cost_rate"]
    
    total_cost = token_cost + agent_cost + premium_cost + compute_cost + doc_cost
    return float(round(total_cost, 2))

def calculate_gross_margin(bill: float, cost: float) -> float:
    """
    Calculates gross margin percentage.
    """
    if bill <= 0:
        return 0.0
    margin = (bill - cost) / bill * 100.0
    return float(round(margin, 2))
