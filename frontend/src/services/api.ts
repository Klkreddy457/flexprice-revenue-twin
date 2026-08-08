import type { 
  SimulationResult, 
  AIAnalysis, 
  FlexpriceDeployment, 
  IngestionStreamLog, 
  IntegrationStatus,
  ProposedPricing
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const API_PREFIX = '/api';
const API_URL = `${API_BASE}${API_PREFIX}`;

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `HTTP Error ${response.status}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return response.json() as Promise<T>;
}

export const api = {
  // Simulations
  async fetchLastSimulation(): Promise<SimulationResult> {
    const res = await fetch(`${API_URL}/simulations/last`);
    return handleResponse<SimulationResult>(res);
  },

  async runSimulation(currentPricingId: string, proposed: ProposedPricing): Promise<SimulationResult> {
    const res = await fetch(`${API_URL}/simulations/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_pricing_id: currentPricingId,
        proposed_pricing: proposed
      })
    });
    return handleResponse<SimulationResult>(res);
  },

  async fetchSimulationDetails(simulationId: string): Promise<SimulationResult> {
    const res = await fetch(`${API_URL}/simulations/${simulationId}`);
    return handleResponse<SimulationResult>(res);
  },

  // Customers
  async fetchCustomers(offset = 0, limit = 100, segment?: string): Promise<{ total: number; customers: any[] }> {
    let url = `${API_URL}/customers/?offset=${offset}&limit=${limit}`;
    if (segment) {
      url += `&segment=${segment}`;
    }
    const res = await fetch(url);
    return handleResponse<{ total: number; customers: any[] }>(res);
  },

  async fetchCustomerDetails(customerId: string, proposed?: ProposedPricing): Promise<any> {
    let url = `${API_URL}/customers/${customerId}`;
    if (proposed) {
      url += `?base_price=${proposed.base_price}&included_units=${proposed.included_units}&overage_price=${proposed.overage_price}`;
    }
    const res = await fetch(url);
    return handleResponse<any>(res);
  },

  // Usage
  async fetchUsageSummary(): Promise<any> {
    const res = await fetch(`${API_URL}/usage/summary`);
    return handleResponse<any>(res);
  },

  // AI Pricing Doctor
  async fetchAIAnalysis(simulationId: string): Promise<AIAnalysis> {
    const res = await fetch(`${API_URL}/ai/pricing-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ simulation_id: simulationId })
    });
    return handleResponse<AIAnalysis>(res);
  },

  // Flexprice Integration
  async deployPricing(pricingModelId: string): Promise<FlexpriceDeployment> {
    const res = await fetch(`${API_URL}/flexprice/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pricing_model_id: pricingModelId })
    });
    return handleResponse<FlexpriceDeployment>(res);
  },

  async fetchFlexpriceLogs(): Promise<IngestionStreamLog[]> {
    const res = await fetch(`${API_URL}/flexprice/stream`);
    return handleResponse<IngestionStreamLog[]>(res);
  },

  async generateFlexpriceEvents(count = 10): Promise<any> {
    const res = await fetch(`${API_URL}/flexprice/generate-events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count })
    });
    return handleResponse<any>(res);
  },

  async fetchFlexpriceStatus(): Promise<IntegrationStatus> {
    const res = await fetch(`${API_URL}/flexprice/status`);
    return handleResponse<IntegrationStatus>(res);
  }
};
