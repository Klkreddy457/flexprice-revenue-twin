from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PricingModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float = Field(..., ge=0)
    included_units: int = Field(..., ge=0)
    overage_price: float = Field(..., ge=0)
    pricing_metric: str = "research_tasks"

class PricingModelCreate(PricingModelBase):
    pass

class PricingModelResponse(PricingModelBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProposedPricing(BaseModel):
    base_price: float = Field(..., ge=0)
    included_units: int = Field(..., ge=0)
    overage_price: float = Field(..., ge=0)
    pricing_metric: str = "research_tasks"

class SimulationRequest(BaseModel):
    current_pricing_id: str
    proposed_pricing: ProposedPricing

class CustomerImpactResponse(BaseModel):
    customer_id: str
    customer_name: str
    segment: str
    current_bill: float
    proposed_bill: float
    bill_change: float
    bill_change_percent: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    usage: int
    margin: float
    infra_cost: float

class RevenueMetrics(BaseModel):
    current: float
    proposed: float
    change: float
    change_percent: float

class CostMetrics(BaseModel):
    current: float
    proposed: float
    change: float

class MarginMetrics(BaseModel):
    current: float
    proposed: float
    change_pp: float

class CustomerStats(BaseModel):
    affected: int
    high_risk: int
    bill_increases: int
    bill_decreases: int
    bill_unchanged: int
    avg_bill_change: float
    median_bill_change: float
    p90_bill_change: float
    p99_bill_change: float

class HealthScore(BaseModel):
    overall: float
    margin: float
    predictability: float
    usage_alignment: float
    heavy_user_risk: float
    revenue_efficiency: float

class SimulationResultResponse(BaseModel):
    simulation_id: str
    name: str
    revenue: RevenueMetrics
    cost: CostMetrics
    margin: MarginMetrics
    customers: CustomerStats
    health_score: HealthScore
    impacts: List[CustomerImpactResponse]
    created_at: datetime

class AIAnalysisRequest(BaseModel):
    simulation_id: str

class RecommendationOption(BaseModel):
    option_name: str
    base_price: float
    included_units: int
    overage_price: float
    revenue: float
    margin: float
    high_risk_customers: int
    explanation: str

class AIAnalysisResponse(BaseModel):
    diagnosis: List[str]
    risks: List[str]
    recommendations: List[RecommendationOption]
    summary: str

class FlexpriceDeployRequest(BaseModel):
    pricing_model_id: str
    live_mode: bool = False

class FlexpriceDeployResponse(BaseModel):
    deployment_id: str
    pricing_model_id: str
    status: str
    details: Dict[str, Any]
    deployed_at: datetime

class UsageEventSimulateRequest(BaseModel):
    count: int = 10
