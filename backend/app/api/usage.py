from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
import pandas as pd

router = APIRouter(prefix="/usage", tags=["Usage"])

@router.get("/summary")
def get_usage_summary(db: Session = Depends(get_db)):
    # Load usage events into a Pandas DataFrame for summary aggregation
    connection = db.bind.connect()
    try:
        df = pd.read_sql(
            "SELECT customer_id, timestamp, tasks, agent_calls, tokens_used, documents_processed, "
            "compute_seconds, premium_model_calls FROM usage_events",
            con=connection
        )
    finally:
        connection.close()

    if df.empty:
        return {
            "totals": {},
            "daily_usage": [],
            "distribution": {}
        }

    # Total counts
    totals = {
        "tasks": int(df['tasks'].sum()),
        "agent_calls": int(df['agent_calls'].sum()),
        "tokens_used": int(df['tokens_used'].sum()),
        "documents_processed": int(df['documents_processed'].sum()),
        "compute_seconds": int(df['compute_seconds'].sum()),
        "premium_model_calls": int(df['premium_model_calls'].sum())
    }

    # Daily aggregation for charts
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date.astype(str)
    
    daily = df.groupby('date').agg({
        'tasks': 'sum',
        'agent_calls': 'sum',
        'tokens_used': 'sum',
        'documents_processed': 'sum',
        'compute_seconds': 'sum',
        'premium_model_calls': 'sum'
    }).reset_index().sort_values(by='date')

    # Convert to list of dicts for frontend charts
    daily_list = daily.to_dict(orient='records')

    # Percentiles distribution of tasks usage per customer per month
    # First group by customer and month
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    cust_monthly = df.groupby(['customer_id', 'month'])['tasks'].sum().reset_index()
    
    percentiles = {
        "p50": float(cust_monthly['tasks'].quantile(0.50)),
        "p75": float(cust_monthly['tasks'].quantile(0.75)),
        "p90": float(cust_monthly['tasks'].quantile(0.90)),
        "p95": float(cust_monthly['tasks'].quantile(0.95)),
        "p99": float(cust_monthly['tasks'].quantile(0.99)),
        "max": int(cust_monthly['tasks'].max()),
        "mean": float(cust_monthly['tasks'].mean()),
        "median": float(cust_monthly['tasks'].median())
    }

    # Segment usage breakdown
    # Let's get customer segments mapping
    from app.db.models import Customer
    customers = db.query(Customer).all()
    cust_seg_map = {c.id: c.segment for c in customers}
    
    df['segment'] = df['customer_id'].map(cust_seg_map)
    seg_breakdown = df.groupby('segment')['tasks'].sum().to_dict()

    return {
        "totals": totals,
        "daily_usage": daily_list,
        "distribution": percentiles,
        "segment_breakdown": seg_breakdown
    }
