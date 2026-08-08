from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import Customer, UsageEvent, PricingModel
from app.services.pricing_service import (
    calculate_monthly_bill,
    calculate_infra_cost,
    calculate_gross_margin
)
from typing import List, Optional
import pandas as pd

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("/")
def get_customers(
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    segment: Optional[str] = None
):
    query = db.query(Customer)
    if segment:
        query = query.filter(Customer.segment == segment)
    
    customers = query.offset(offset).limit(limit).all()
    total = query.count()
    
    # Return customers list
    return {
        "total": total,
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "segment": c.segment,
                "created_at": c.created_at
            }
            for c in customers
        ]
    }

@router.get("/{customer_id}")
def get_customer_details(
    customer_id: str,
    db: Session = Depends(get_db),
    base_price: float = 49.00,
    included_units: int = 100,
    overage_price: float = 0.75
):
    customer = db.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Get all events for customer
    connection = db.bind.connect()
    try:
        df = pd.read_sql(
            f"SELECT timestamp, tasks, agent_calls, tokens_used, documents_processed, "
            f"compute_seconds, premium_model_calls FROM usage_events WHERE customer_id = '{customer_id}'",
            con=connection
        )
    finally:
        connection.close()

    if df.empty:
        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "segment": customer.segment
            },
            "usage_totals": {},
            "billing_comparison": {}
        }

    # Group usage by month
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    
    monthly_agg = df.groupby('month').agg({
        'tasks': 'sum',
        'agent_calls': 'sum',
        'tokens_used': 'sum',
        'documents_processed': 'sum',
        'compute_seconds': 'sum',
        'premium_model_calls': 'sum'
    }).reset_index()

    # Get default/current Pro pricing
    default_pm = db.query(PricingModel).filter_by(id="pm_pro_default").first()
    curr_base = default_pm.base_price if default_pm else 49.00
    curr_inc = default_pm.included_units if default_pm else 100
    curr_over = default_pm.overage_price if default_pm else 0.75

    monthly_details = []
    total_tasks = 0
    total_agent_calls = 0
    total_tokens = 0
    total_docs = 0
    total_compute = 0
    total_premium = 0
    
    total_current_bill = 0.0
    total_proposed_bill = 0.0
    total_infra_cost = 0.0

    for _, row in monthly_agg.iterrows():
        m = row['month']
        tasks = int(row['tasks'])
        calls = int(row['agent_calls'])
        toks = int(row['tokens_used'])
        docs = int(row['documents_processed'])
        comp = int(row['compute_seconds'])
        prem = int(row['premium_model_calls'])

        # Aggregate totals
        total_tasks += tasks
        total_agent_calls += calls
        total_tokens += toks
        total_docs += docs
        total_compute += comp
        total_premium += prem

        curr_bill = calculate_monthly_bill(tasks, curr_base, curr_inc, curr_over)
        prop_bill = calculate_monthly_bill(tasks, base_price, included_units, overage_price)
        infra_cost = calculate_infra_cost(toks, calls, prem, comp, docs)

        total_current_bill += curr_bill
        total_proposed_bill += prop_bill
        total_infra_cost += infra_cost

        monthly_details.append({
            "month": m,
            "tasks": tasks,
            "agent_calls": calls,
            "tokens_used": toks,
            "documents_processed": docs,
            "compute_seconds": comp,
            "premium_model_calls": prem,
            "current_bill": curr_bill,
            "proposed_bill": prop_bill,
            "infra_cost": infra_cost,
            "margin": calculate_gross_margin(prop_bill, infra_cost)
        })

    # Mathematical explanation of the bill change
    # Focus on the last month or average monthly difference
    explanation = ""
    avg_tasks_per_month = total_tasks / len(monthly_agg) if len(monthly_agg) > 0 else 0
    
    bill_diff = total_proposed_bill - total_current_bill
    
    if bill_diff > 0.01:
        # Bill increased
        if avg_tasks_per_month > included_units:
            overage_tasks = avg_tasks_per_month - included_units
            explanation = (
                f"This customer's bill increased primarily because their average monthly usage of "
                f"{avg_tasks_per_month:.1f} tasks exceeds the new proposed plan limit of {included_units} tasks, "
                f"resulting in approximately {overage_tasks:.1f} overage tasks charged at ${overage_price:.2f}/task."
            )
        else:
            explanation = (
                f"This customer's bill increased because the proposed subscription price is higher "
                f"than current, and their usage did not trigger enough overage reductions to offset it."
            )
    elif bill_diff < -0.01:
        # Bill decreased
        savings = abs(bill_diff)
        explanation = (
            f"This customer saves ${savings:.2f} overall. The savings are driven by the lower proposed "
            f"base subscription price (${base_price:.2f} vs ${curr_base:.2f}) and cheaper overage fees "
            f"(${overage_price:.2f}/task vs ${curr_over:.2f}/task)."
        )
    else:
        explanation = "This customer's bill remains unchanged as their usage falls entirely within the limits of both models."

    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "segment": customer.segment,
            "created_at": customer.created_at
        },
        "totals": {
            "tasks": total_tasks,
            "agent_calls": total_agent_calls,
            "tokens_used": total_tokens,
            "documents_processed": total_docs,
            "compute_seconds": total_compute,
            "premium_model_calls": total_premium,
            "current_bill": round(total_current_bill, 2),
            "proposed_bill": round(total_proposed_bill, 2),
            "bill_change": round(bill_diff, 2),
            "bill_change_percent": round((bill_diff / total_current_bill * 100.0) if total_current_bill > 0 else 0.0, 2),
            "infra_cost": round(total_infra_cost, 2),
            "margin": calculate_gross_margin(total_proposed_bill, total_infra_cost)
        },
        "monthly_details": monthly_details,
        "change_explanation": explanation
    }
