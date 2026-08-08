export interface Customer {
  id: string;
  name: string;
  segment: string;
  created_at: string;
}

export interface PricingModel {
  id: string;
  name: string;
  description?: string;
  base_price: number;
  included_units: number;
  overage_price: number;
  pricing_metric: string;
  created_at: string;
}

export interface ProposedPricing {
  base_price: number;
  included_units: number;
  overage_price: number;
  pricing_metric: string;
}

export interface CustomerImpact {
  customer_id: string;
  customer_name: string;
  segment: string;
  current_bill: number;
  proposed_bill: number;
  bill_change: number;
  bill_change_percent: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  usage: number;
  margin: number;
  infra_cost: number;
}

export interface RevenueMetrics {
  current: number;
  proposed: number;
  change: number;
  change_percent: number;
}

export interface CostMetrics {
  current: number;
  proposed: number;
  change: number;
}

export interface MarginMetrics {
  current: number;
  proposed: number;
  change_pp: number;
}

export interface CustomerStats {
  affected: number;
  high_risk: number;
  bill_increases: number;
  bill_decreases: number;
  bill_unchanged: number;
  avg_bill_change: number;
  median_bill_change: number;
  p90_bill_change: number;
  p99_bill_change: number;
}

export interface HealthScore {
  overall: number;
  margin: number;
  predictability: number;
  usage_alignment: number;
  heavy_user_risk: number;
  revenue_efficiency: number;
}

export interface SimulationResult {
  simulation_id: string;
  name: string;
  revenue: RevenueMetrics;
  cost: CostMetrics;
  margin: MarginMetrics;
  customers: CustomerStats;
  health_score: HealthScore;
  impacts: CustomerImpact[];
  created_at: string;
}

export interface RecommendationOption {
  option_name: string;
  base_price: number;
  included_units: number;
  overage_price: number;
  revenue: number;
  margin: number;
  high_risk_customers: number;
  explanation: string;
}

export interface AIAnalysis {
  diagnosis: string[];
  risks: string[];
  recommendations: RecommendationOption[];
  summary: string;
}

export interface DeploymentLog {
  step: string;
  endpoint: string;
  payload: any;
  status: string;
  response?: any;
}

export interface FlexpriceDeployment {
  deployment_id: string;
  pricing_model_id: string;
  status: string;
  details: {
    deployment_id: string;
    mode: string;
    status: string;
    entities: any;
    api_call_logs: DeploymentLog[];
  };
  deployed_at: string;
}

export interface IngestionStreamLog {
  timestamp: string;
  customer_id: string;
  customer_name: string;
  event_name: string;
  usage: string;
  status: string;
  mode: string;
}

export interface IntegrationStatus {
  mode: 'LIVE' | 'DEMO';
  url: string;
  configured: boolean;
}
