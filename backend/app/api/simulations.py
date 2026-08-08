from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import Simulation, SimulationResult, CustomerImpact, PricingModel
from app.db.schemas import SimulationRequest, SimulationResultResponse
from app.services.simulation_service import run_pricing_simulation
from typing import List

router = APIRouter(prefix="/simulations", tags=["Simulations"])

@router.post("/", response_model=SimulationResultResponse)
def create_simulation(req: SimulationRequest, db: Session = Depends(get_db)):
    try:
        results = run_pricing_simulation(
            db=db,
            current_pricing_id=req.current_pricing_id,
            proposed_base_price=req.proposed_pricing.base_price,
            proposed_included_units=req.proposed_pricing.included_units,
            proposed_overage_price=req.proposed_pricing.overage_price,
            pricing_metric=req.proposed_pricing.pricing_metric,
            simulation_name=f"Sim {req.proposed_pricing.base_price}/{req.proposed_pricing.included_units}/{req.proposed_pricing.overage_price}"
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation run failed: {str(e)}")

@router.get("/last", response_model=SimulationResultResponse)
def get_last_simulation(db: Session = Depends(get_db)):
    last_sim = db.query(Simulation).order_by(Simulation.created_at.desc()).first()
    if not last_sim:
        # If no simulations exist, let's run one with default parameters so the page is never blank
        # Pro defaults: $49/mo, 100 tasks, $0.75 overage. Proposed: same as current.
        try:
            results = run_pricing_simulation(
                db=db,
                current_pricing_id="pm_pro_default",
                proposed_base_price=49.00,
                proposed_included_units=100,
                proposed_overage_price=0.75,
                pricing_metric="research_tasks",
                simulation_name="Default Initial Run"
            )
            return results
        except Exception as e:
            raise HTTPException(status_code=404, detail="No simulations found and default failed to run.")
            
    return get_simulation_details(last_sim.id, db)

@router.get("/{simulation_id}", response_model=SimulationResultResponse)
def get_simulation_details(simulation_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
        
    res = db.query(SimulationResult).filter_by(simulation_id=simulation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Simulation results not found")
        
    impacts = db.query(CustomerImpact).filter_by(simulation_id=simulation_id).all()
    
    # Map to schema response
    summary = res.summary_data
    
    # We need to fetch customer info to populate impact details
    from app.db.models import Customer
    customers = db.query(Customer).all()
    cust_map = {c.id: {"name": c.name, "segment": c.segment} for c in customers}
    
    # Query aggregated usage to fetch tasks and average margins
    # Let's rebuild the impacts response list from the customer impacts table
    # Wait, we can fetch tasks count from the impacts or compute it.
    # In the db, we store CustomerImpact. Let's map it.
    impact_list = []
    for imp in impacts:
        cust_info = cust_map.get(imp.customer_id, {"name": "Unknown", "segment": "Unknown"})
        
        # Calculate bill change percentage
        curr = imp.current_bill
        prop = imp.proposed_bill
        change = imp.bill_change
        pct = (change / curr * 100.0) if curr > 0 else 0.0
        
        impact_list.append({
            "customer_id": imp.customer_id,
            "customer_name": cust_info["name"],
            "segment": cust_info["segment"],
            "current_bill": round(curr, 2),
            "proposed_bill": round(prop, 2),
            "bill_change": round(change, 2),
            "bill_change_percent": round(pct, 2),
            "risk_level": imp.risk_level,
            "usage": 0, # Placeholder if not loaded, or load below
            "margin": 0.0,
            "infra_cost": 0.0
        })
        
    # We can load actual usage stats for high fidelity detail
    import pandas as pd
    try:
        connection = db.bind.connect()
        df = pd.read_sql(f"SELECT customer_id, SUM(tasks) as total_tasks FROM usage_events GROUP BY customer_id", con=connection)
        connection.close()
        tasks_map = dict(zip(df['customer_id'], df['total_tasks']))
        for item in impact_list:
            item["usage"] = int(tasks_map.get(item["customer_id"], 0))
    except Exception:
        pass

    return {
        "simulation_id": sim.id,
        "name": sim.name,
        "revenue": summary["revenue"],
        "cost": summary["cost"],
        "margin": summary["margin"],
        "customers": summary["customers"],
        "health_score": summary["health_score"],
        "impacts": impact_list,
        "created_at": sim.created_at
    }
