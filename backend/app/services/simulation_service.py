import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db.models import Customer, UsageEvent, PricingModel, CustomerImpact, Simulation, SimulationResult
from app.services.pricing_service import (
    calculate_monthly_bill,
    calculate_infra_cost,
    calculate_gross_margin
)
import datetime
import uuid

def run_pricing_simulation(
    db: Session,
    current_pricing_id: str,
    proposed_base_price: float,
    proposed_included_units: int,
    proposed_overage_price: float,
    pricing_metric: str = "research_tasks",
    simulation_name: str = "Pricing Simulation",
    persist: bool = True
) -> Dict[str, Any]:
    """
    Runs pricing simulation on historical usage data.
    """
    # 1. Fetch current pricing model
    current_pm = db.query(PricingModel).filter_by(id=current_pricing_id).first()
    if not current_pm:
        raise ValueError(f"Current pricing model {current_pricing_id} not found.")

    # 2. Get all customers and map them
    customers = db.query(Customer).all()
    cust_map = {c.id: {"name": c.name, "segment": c.segment} for c in customers}

    # 3. Load usage events into a Pandas DataFrame for database-agnostic aggregation
    # Query only the required columns to save memory
    connection = db.bind.connect()
    try:
        df = pd.read_sql(
            "SELECT customer_id, timestamp, tasks, agent_calls, tokens_used, "
            "documents_processed, compute_seconds, premium_model_calls FROM usage_events",
            con=connection
        )
    finally:
        connection.close()

    if df.empty:
        # Return empty simulation structure
        return _empty_simulation_result(simulation_name)

    # 4. Group by customer and month
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)

    agg = df.groupby(['customer_id', 'month']).agg({
        'tasks': 'sum',
        'agent_calls': 'sum',
        'tokens_used': 'sum',
        'documents_processed': 'sum',
        'compute_seconds': 'sum',
        'premium_model_calls': 'sum'
    }).reset_index()

    # 5. Compute bills and infra costs for each customer-month
    customer_months_results = []
    for _, row in agg.iterrows():
        cust_id = row['customer_id']
        month = row['month']
        tasks = int(row['tasks'])
        
        # Calculate bills
        curr_bill = calculate_monthly_bill(
            tasks, current_pm.base_price, current_pm.included_units, current_pm.overage_price
        )
        prop_bill = calculate_monthly_bill(
            tasks, proposed_base_price, proposed_included_units, proposed_overage_price
        )
        
        # Calculate infra cost
        infra_cost = calculate_infra_cost(
            tokens_used=int(row['tokens_used']),
            agent_calls=int(row['agent_calls']),
            premium_model_calls=int(row['premium_model_calls']),
            compute_seconds=int(row['compute_seconds']),
            documents_processed=int(row['documents_processed'])
        )
        
        customer_months_results.append({
            "customer_id": cust_id,
            "month": month,
            "tasks": tasks,
            "current_bill": curr_bill,
            "proposed_bill": prop_bill,
            "infra_cost": infra_cost
        })

    cm_df = pd.DataFrame(customer_months_results)

    # 6. Aggregate results per customer (summing bills and cost over all 3 months)
    cust_agg = cm_df.groupby('customer_id').agg({
        'tasks': 'sum',
        'current_bill': 'sum',
        'proposed_bill': 'sum',
        'infra_cost': 'sum'
    }).reset_index()

    # 7. Merge customer info (segment, name)
    cust_agg['name'] = cust_agg['customer_id'].map(lambda cid: cust_map.get(cid, {}).get("name", "Unknown"))
    cust_agg['segment'] = cust_agg['customer_id'].map(lambda cid: cust_map.get(cid, {}).get("segment", "Unknown"))

    # Calculate change metrics per customer
    cust_agg['bill_change'] = cust_agg['proposed_bill'] - cust_agg['current_bill']
    cust_agg['bill_change_percent'] = np.where(
        cust_agg['current_bill'] > 0,
        (cust_agg['bill_change'] / cust_agg['current_bill']) * 100.0,
        0.0
    )
    cust_agg['margin'] = np.where(
        cust_agg['proposed_bill'] > 0,
        ((cust_agg['proposed_bill'] - cust_agg['infra_cost']) / cust_agg['proposed_bill']) * 100.0,
        0.0
    )
    
    # Assign risk levels
    def get_risk_level(row):
        pct = row['bill_change_percent']
        if pct >= 50.0:
            return "CRITICAL"
        elif pct >= 25.0:
            return "HIGH"
        elif pct > 0.0:
            return "MEDIUM"
        else:
            return "LOW"

    cust_agg['risk_level'] = cust_agg.apply(get_risk_level, axis=1)

    # 8. Calculate total summary metrics
    total_curr_rev = float(cust_agg['current_bill'].sum())
    total_prop_rev = float(cust_agg['proposed_bill'].sum())
    total_infra_cost = float(cust_agg['infra_cost'].sum())
    
    rev_change = total_prop_rev - total_curr_rev
    rev_pct = (rev_change / total_curr_rev * 100.0) if total_curr_rev > 0 else 0.0
    
    curr_margin = ((total_curr_rev - total_infra_cost) / total_curr_rev * 100.0) if total_curr_rev > 0 else 0.0
    prop_margin = ((total_prop_rev - total_infra_cost) / total_prop_rev * 100.0) if total_prop_rev > 0 else 0.0
    margin_change_pp = prop_margin - curr_margin

    # Customers stats
    bill_increases = int((cust_agg['bill_change'] > 0.01).sum())
    bill_decreases = int((cust_agg['bill_change'] < -0.01).sum())
    bill_unchanged = int((cust_agg['bill_change'].abs() <= 0.01).sum())
    affected = bill_increases + bill_decreases
    high_risk = int(cust_agg['risk_level'].isin(["HIGH", "CRITICAL"]).sum())

    # Bill change stats
    avg_bill_change = float(cust_agg['bill_change'].mean())
    median_bill_change = float(cust_agg['bill_change'].median())
    p90_bill_change = float(cust_agg['bill_change'].quantile(0.90))
    p99_bill_change = float(cust_agg['bill_change'].quantile(0.99))

    # 9. Deterministic Pricing Health Score
    # Score 0 - 100
    # Margin Health: optimal > 50% proposed margin
    margin_score = min(100.0, max(0.0, (prop_margin - 10.0) * 2.0)) # e.g. 50% margin gives 80, 60% gives 100
    
    # Predictability: penalized by high/critical risk customers (e.g. 100 - 3 * % of high/crit users)
    high_risk_pct = (high_risk / len(cust_agg) * 100.0) if len(cust_agg) > 0 else 0.0
    predictability_score = max(0.0, min(100.0, 100.0 - (high_risk_pct * 4.0)))

    # Usage Alignment: Are we capturing overages effectively without overcharging everyone?
    # Ideally, 20-30% of customers exceed included units. If 90% exceed, it's a pricing cliff/overage trap. If 1% exceed, base is too high/inefficient.
    # Check what % of customers exceed the proposed included units in their average monthly tasks.
    exceeded_count = 0
    for _, row in cm_df.iterrows():
        if row['tasks'] > proposed_included_units:
            exceeded_count += 1
    exceeded_pct = (exceeded_count / len(cm_df) * 100.0) if len(cm_df) > 0 else 0.0
    
    # Peak score at 25% exceeded.
    usage_alignment_score = max(0.0, 100.0 - abs(exceeded_pct - 25.0) * 2.5)

    # Heavy User Risk: Revenue concentration.
    # If top 5% of customers generate > 50% of proposed revenue, it's high concentration risk.
    top_5_percent_count = max(1, int(len(cust_agg) * 0.05))
    top_revenue = cust_agg.sort_values(by="proposed_bill", ascending=False).head(top_5_percent_count)["proposed_bill"].sum()
    rev_concentration = (top_revenue / total_prop_rev * 100.0) if total_prop_rev > 0 else 0.0
    # Ideal concentration is <40%. Penalty for higher concentration.
    heavy_user_risk_score = max(0.0, min(100.0, 100.0 - max(0.0, rev_concentration - 30.0) * 1.5))

    # Revenue Efficiency: Total proposed revenue relative to total infrastructure cost
    rev_to_cost_ratio = (total_prop_rev / total_infra_cost) if total_infra_cost > 0 else 1.0
    # Ideal ratio >= 2.0 (representing 50% gross margin)
    revenue_efficiency_score = min(100.0, max(0.0, (rev_to_cost_ratio - 1.0) * 100.0))

    overall_health = (margin_score + predictability_score + usage_alignment_score + heavy_user_risk_score + revenue_efficiency_score) / 5.0

    # 10. Compile final structure
    simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
    
    results = {
        "simulation_id": simulation_id,
        "name": simulation_name,
        "revenue": {
            "current": round(total_curr_rev, 2),
            "proposed": round(total_prop_rev, 2),
            "change": round(rev_change, 2),
            "change_percent": round(rev_pct, 2)
        },
        "cost": {
            "current": round(total_infra_cost, 2),
            "proposed": round(total_infra_cost, 2),
            "change": 0.0
        },
        "margin": {
            "current": round(curr_margin, 2),
            "proposed": round(prop_margin, 2),
            "change_pp": round(margin_change_pp, 2)
        },
        "customers": {
            "affected": affected,
            "high_risk": high_risk,
            "bill_increases": bill_increases,
            "bill_decreases": bill_decreases,
            "bill_unchanged": bill_unchanged,
            "avg_bill_change": round(avg_bill_change, 2),
            "median_bill_change": round(median_bill_change, 2),
            "p90_bill_change": round(p90_bill_change, 2),
            "p99_bill_change": round(p99_bill_change, 2)
        },
        "health_score": {
            "overall": round(overall_health, 2),
            "margin": round(margin_score, 2),
            "predictability": round(predictability_score, 2),
            "usage_alignment": round(usage_alignment_score, 2),
            "heavy_user_risk": round(heavy_user_risk_score, 2),
            "revenue_efficiency": round(revenue_efficiency_score, 2)
        },
        "impacts": [
            {
                "customer_id": row["customer_id"],
                "customer_name": row["name"],
                "segment": row["segment"],
                "current_bill": round(row["current_bill"], 2),
                "proposed_bill": round(row["proposed_bill"], 2),
                "bill_change": round(row["bill_change"], 2),
                "bill_change_percent": round(row["bill_change_percent"], 2),
                "risk_level": row["risk_level"],
                "usage": int(row["tasks"]),
                "margin": round(row["margin"], 2),
                "infra_cost": round(row["infra_cost"], 2)
            }
            for _, row in cust_agg.iterrows()
        ],
        "created_at": datetime.datetime.utcnow()
    }

    if persist:
        # 11. Save Simulation and Results to Database inside a single transaction
        try:
            sim_obj = Simulation(
                id=simulation_id,
                name=simulation_name,
                current_pricing_id=current_pricing_id,
                proposed_pricing_data={
                    "base_price": proposed_base_price,
                    "included_units": proposed_included_units,
                    "overage_price": proposed_overage_price,
                    "pricing_metric": pricing_metric
                },
                created_at=results["created_at"]
            )
            db.add(sim_obj)
            db.flush()  # Ensure Simulation is inserted before dependent records to satisfy foreign key constraints

            # Save summary result
            # Convert created_at and other datetimes to ISO strings for JSON serialization
            summary_to_save = results.copy()
            summary_to_save.pop("impacts") # Don't store impacts list in summary JSON to keep DB small
            summary_to_save["created_at"] = summary_to_save["created_at"].isoformat()
            
            result_obj = SimulationResult(
                id=f"res_{uuid.uuid4().hex[:8]}",
                simulation_id=simulation_id,
                summary_data=summary_to_save,
                status="completed",
                created_at=results["created_at"]
            )
            db.add(result_obj)
            db.flush()  # Ensure SimulationResult is inserted only after Simulation exists

            # Save customer impacts bulk
            impacts_to_db = [
                CustomerImpact(
                    id=f"imp_{uuid.uuid4().hex[:8]}",
                    simulation_id=simulation_id,
                    customer_id=imp["customer_id"],
                    current_bill=imp["current_bill"],
                    proposed_bill=imp["proposed_bill"],
                    bill_change=imp["bill_change"],
                    risk_level=imp["risk_level"]
                )
                for imp in results["impacts"]
            ]
            db.add_all(impacts_to_db)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    return results

def _empty_simulation_result(name: str) -> Dict[str, Any]:
    return {
        "simulation_id": "sim_empty",
        "name": name,
        "revenue": {"current": 0.0, "proposed": 0.0, "change": 0.0, "change_percent": 0.0},
        "cost": {"current": 0.0, "proposed": 0.0, "change": 0.0},
        "margin": {"current": 0.0, "proposed": 0.0, "change_pp": 0.0},
        "customers": {
            "affected": 0, "high_risk": 0, "bill_increases": 0, "bill_decreases": 0, "bill_unchanged": 0,
            "avg_bill_change": 0.0, "median_bill_change": 0.0, "p90_bill_change": 0.0, "p99_bill_change": 0.0
        },
        "health_score": {
            "overall": 0.0, "margin": 0.0, "predictability": 0.0, "usage_alignment": 0.0, 
            "heavy_user_risk": 0.0, "revenue_efficiency": 0.0
        },
        "impacts": [],
        "created_at": datetime.datetime.utcnow()
    }
