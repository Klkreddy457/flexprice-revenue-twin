from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import Simulation, SimulationResult, PricingModel
from app.db.schemas import AIAnalysisRequest, AIAnalysisResponse
from app.services.simulation_service import run_pricing_simulation
from app.services.ai_service import analyze_simulation_with_ai

router = APIRouter(prefix="/ai", tags=["AI Pricing Doctor"])

@router.post("/pricing-analysis", response_model=AIAnalysisResponse)
async def get_pricing_analysis(req: AIAnalysisRequest, db: Session = Depends(get_db)):
    # 1. Fetch the simulation
    sim = db.query(Simulation).filter_by(id=req.simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    res = db.query(SimulationResult).filter_by(simulation_id=req.simulation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Simulation result not found")
        
    current_pricing_id = sim.current_pricing_id
    current_pm = db.query(PricingModel).filter_by(id=current_pricing_id).first()
    if not current_pm:
        raise HTTPException(status_code=404, detail="Current pricing model not found")

    # Reconstruct/read summary metrics
    metrics = res.summary_data

    # 2. Programmatically generate 3 candidate models based on current pricing
    # Option A (Value Focus)
    opt_a_base = round(current_pm.base_price * 0.8, 0) - 1.0  # e.g., $39
    opt_a_inc = int(current_pm.included_units * 0.75)         # e.g., 75
    opt_a_over = round(current_pm.overage_price * 1.07, 2)    # e.g., $0.80

    # Option B (Balanced / Recommended)
    opt_b_base = float(current_pm.base_price)                  # e.g., $49
    opt_b_inc = int(current_pm.included_units * 1.25)         # e.g., 125
    opt_b_over = round(current_pm.overage_price * 0.73, 2)    # e.g., $0.55

    # Option C (Premium / Overage Protection)
    opt_c_base = round(current_pm.base_price * 1.4, 0) + 1.0  # e.g., $69
    opt_c_inc = int(current_pm.included_units * 2.0)          # e.g., 200
    opt_c_over = round(current_pm.overage_price * 0.60, 2)    # e.g., $0.45

    # 3. Simulate all 3 candidates in-memory (persist=False)
    try:
        cand_a_sim = run_pricing_simulation(
            db=db,
            current_pricing_id=current_pricing_id,
            proposed_base_price=opt_a_base,
            proposed_included_units=opt_a_inc,
            proposed_overage_price=opt_a_over,
            simulation_name="Candidate Option A",
            persist=False
        )
        cand_a_sim["base_price"] = opt_a_base
        cand_a_sim["included_units"] = opt_a_inc
        cand_a_sim["overage_price"] = opt_a_over
        cand_a_sim["name"] = f"Value Plan (${opt_a_base}/mo, {opt_a_inc} tasks)"

        cand_b_sim = run_pricing_simulation(
            db=db,
            current_pricing_id=current_pricing_id,
            proposed_base_price=opt_b_base,
            proposed_included_units=opt_b_inc,
            proposed_overage_price=opt_b_over,
            simulation_name="Candidate Option B",
            persist=False
        )
        cand_b_sim["base_price"] = opt_b_base
        cand_b_sim["included_units"] = opt_b_inc
        cand_b_sim["overage_price"] = opt_b_over
        cand_b_sim["name"] = f"Balanced Plan (${opt_b_base}/mo, {opt_b_inc} tasks)"

        cand_c_sim = run_pricing_simulation(
            db=db,
            current_pricing_id=current_pricing_id,
            proposed_base_price=opt_c_base,
            proposed_included_units=opt_c_inc,
            proposed_overage_price=opt_c_over,
            simulation_name="Candidate Option C",
            persist=False
        )
        cand_c_sim["base_price"] = opt_c_base
        cand_c_sim["included_units"] = opt_c_inc
        cand_c_sim["overage_price"] = opt_c_over
        cand_c_sim["name"] = f"Premium Plan (${opt_c_base}/mo, {opt_c_inc} tasks)"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"In-memory optimization simulation failed: {str(e)}")

    # 4. Invoke LLM analyze function
    candidates = [cand_a_sim, cand_b_sim, cand_c_sim]
    analysis = await analyze_simulation_with_ai(metrics, candidates)

    return analysis
