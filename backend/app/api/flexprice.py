from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.db.models import PricingModel, FlexpriceDeployment, Customer
from app.db.schemas import FlexpriceDeployRequest, FlexpriceDeployResponse, UsageEventSimulateRequest
from app.services.flexprice_service import flexprice_service
import random
import datetime

router = APIRouter(prefix="/flexprice", tags=["Flexprice Integration"])

@router.post("/deploy", response_model=FlexpriceDeployResponse)
async def deploy_pricing(req: FlexpriceDeployRequest, db: Session = Depends(get_db)):
    # 1. Fetch the pricing model
    pm = db.query(PricingModel).filter_by(id=req.pricing_model_id).first()
    if not pm:
        # Check if the pricing model ID corresponds to a simulation.
        # If it is from a simulation proposed pricing, we might need to create it.
        # Let's see: if we pass parameters or if the ID is pm_pro_default, we fetch it.
        # If it's a simulation, we can lookup the simulation's proposed pricing and create a temporary pricing model record.
        from app.db.models import Simulation
        sim = db.query(Simulation).order_by(Simulation.created_at.desc()).first()
        if sim:
            prop = sim.proposed_pricing_data
            pm = PricingModel(
                id=req.pricing_model_id,
                name=f"Proposed Pricing ({req.pricing_model_id})",
                description=f"Simulated proposed pricing deployed to Flexprice",
                base_price=prop["base_price"],
                included_units=prop["included_units"],
                overage_price=prop["overage_price"],
                pricing_metric=prop["pricing_metric"]
            )
            db.add(pm)
            db.commit()
            db.refresh(pm)
        else:
            raise HTTPException(status_code=404, detail="Pricing model or current simulation not found")

    # 2. Deploy to Flexprice API / Mock
    try:
        deployment_res = await flexprice_service.deploy_pricing_to_flexprice(
            base_price=pm.base_price,
            included_units=pm.included_units,
            overage_price=pm.overage_price,
            plan_name=pm.name,
            pricing_metric=pm.pricing_metric
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flexprice deployment request failed: {str(e)}")

    # 3. Save deployment to DB
    dep_obj = FlexpriceDeployment(
        id=deployment_res["deployment_id"],
        pricing_model_id=pm.id,
        status="active" if deployment_res["status"] == "success" else "failed",
        details=deployment_res,
        deployed_at=datetime.datetime.utcnow()
    )
    db.add(dep_obj)
    db.commit()
    db.refresh(dep_obj)

    return {
        "deployment_id": dep_obj.id,
        "pricing_model_id": dep_obj.pricing_model_id,
        "status": dep_obj.status,
        "details": dep_obj.details,
        "deployed_at": dep_obj.deployed_at
    }

@router.get("/stream")
def get_live_stream_logs():
    """
    Returns the last 50 ingestion logs from the live stream.
    """
    # If the log stream is empty, pre-populate it with 5 items so it is never empty in demo
    if not flexprice_service.simulated_stream_logs:
        flexprice_service.simulated_stream_logs = [
            {
                "timestamp": (datetime.datetime.utcnow() - datetime.timedelta(seconds=i*30)).isoformat(),
                "customer_id": f"cust_{random.randint(1,1000):04d}",
                "customer_name": f"Nova Labs {i}",
                "event_name": "research_completed",
                "usage": f"1 task, {random.randint(5,15)} calls, {random.randint(5000,50000)} tokens",
                "status": "success",
                "mode": flexprice_service.get_mode()
            }
            for i in range(5)
        ]
    return flexprice_service.simulated_stream_logs

@router.post("/generate-events")
async def generate_simulated_events(req: UsageEventSimulateRequest, db: Session = Depends(get_db)):
    """
    Generates usage events for random customers and streams them.
    """
    customers = db.query(Customer).all()
    if not customers:
        raise HTTPException(status_code=400, detail="No customers found. Database must be seeded first.")
        
    results = []
    for _ in range(req.count):
        cust = random.choice(customers)
        tasks = 1
        agent_calls = random.randint(3, 25)
        tokens_used = random.randint(3000, 120000)
        documents_processed = random.randint(0, 8)
        compute_seconds = random.randint(10, 450)
        premium_model_calls = random.choice([0, 0, 0, 1, 3, 10]) # Weighted towards 0

        res = await flexprice_service.ingest_usage_event(
            customer_id=cust.id,
            customer_name=cust.name,
            tasks=tasks,
            agent_calls=agent_calls,
            tokens_used=tokens_used,
            documents_processed=documents_processed,
            compute_seconds=compute_seconds,
            premium_model_calls=premium_model_calls
        )
        results.append(res)
        
    return {
        "status": "success",
        "generated_count": req.count,
        "results": results[:5] # Return first 5 results summary
    }

@router.get("/status")
def get_integration_status():
    """
    Returns API connection credentials state.
    """
    return {
        "mode": flexprice_service.get_mode(),
        "url": flexprice_service.base_url,
        "configured": settings.FLEXPRICE_API_KEY is not None and settings.FLEXPRICE_API_KEY != ""
    }
