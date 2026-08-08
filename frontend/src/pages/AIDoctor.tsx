import React, { useState } from 'react';
import { api } from '../services/api';
import type { SimulationResult, AIAnalysis, ProposedPricing } from '../types';
import { 
  Sparkles, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  Loader2,
  AlertCircle
} from 'lucide-react';

interface AIDoctorProps {
  simResult: SimulationResult | null;
  setProposed: React.Dispatch<React.SetStateAction<ProposedPricing>>;
  onNavigate: (tab: string) => void;
  // Trigger simulation rerun in App.tsx
  triggerSimulation: (pricing: ProposedPricing) => Promise<void>;
}

export const AIDoctor: React.FC<AIDoctorProps> = ({ 
  simResult, 
  setProposed, 
  onNavigate,
  triggerSimulation
}) => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConsultDoctor = async () => {
    if (!simResult) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.fetchAIAnalysis(simResult.simulation_id);
      setAnalysis(res);
    } catch (err: any) {
      setError(err.message || 'AI consultation request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRecommendation = async (rec: any) => {
    const newPricing: ProposedPricing = {
      base_price: rec.base_price,
      included_units: rec.included_units,
      overage_price: rec.overage_price,
      pricing_metric: 'research_tasks'
    };
    
    // 1. Update sliders state
    setProposed(newPricing);
    
    // 2. Trigger rerun in backend so comparison stats update
    await triggerSimulation(newPricing);
    
    // 3. Navigate back to Revenue Twin dashboard
    onNavigate('revenue-twin');
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="h-7 w-7 text-blue-400" />
          AI Pricing Doctor
        </h1>
        <p className="text-sm text-muted-foreground">
          Diagnose monetization leakages and examine optimized alternative plans evaluated deterministically.
        </p>
      </div>

      {!simResult ? (
        <div className="rounded-lg border bg-card p-12 text-center flex flex-col items-center justify-center min-h-[350px]">
          <AlertCircle className="h-10 w-10 text-muted-foreground mb-3" />
          <h3 className="font-semibold text-lg">Simulation Context Missing</h3>
          <p className="text-sm text-muted-foreground max-w-md mt-1 mb-4">
            You must run a pricing simulation on the Revenue Twin workspace first before consulting the AI doctor.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Simulation Summary panel */}
          <div className="rounded-lg border bg-slate-900/30 p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1">
              <h3 className="font-semibold text-base">Simulation Context: {simResult.name}</h3>
              <p className="text-xs text-muted-foreground">
                Revenue: ${simResult.revenue.proposed.toLocaleString()} ({simResult.revenue.change_percent >= 0 ? '+' : ''}{simResult.revenue.change_percent}%) • Gross Margin: {simResult.margin.proposed.toFixed(1)}% ({simResult.margin.change_pp >= 0 ? '+' : ''}{simResult.margin.change_pp.toFixed(1)}pp) • High Risk: {simResult.customers.high_risk} accounts
              </p>
            </div>
            
            <button
              onClick={handleConsultDoctor}
              disabled={loading}
              className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded bg-white text-black font-semibold text-sm hover:bg-slate-200 transition-colors disabled:bg-slate-800 disabled:text-slate-400 shrink-0"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing Platform Metrics...
                </>
              ) : (
                <>
                  <Activity className="h-4 w-4" />
                  Consult AI Pricing Doctor
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="text-sm text-red-400 bg-red-950/20 border border-red-900/30 p-4 rounded-lg">
              {error}
            </div>
          )}

          {/* AI Result presentation */}
          {analysis && (
            <div className="space-y-8 animate-in fade-in duration-300">
              
              {/* Executive Summary */}
              <div className="rounded-lg border bg-card p-6 space-y-3">
                <h3 className="font-semibold text-lg border-b pb-2">Strategic Diagnostic Summary</h3>
                <p className="text-sm text-slate-300 leading-relaxed font-medium">
                  {analysis.summary}
                </p>
              </div>

              {/* Diagnoses and Risks grid */}
              <div className="grid gap-6 md:grid-cols-2">
                {/* Diagnoses list */}
                <div className="rounded-lg border bg-card p-6 space-y-4">
                  <h3 className="font-semibold text-base border-b pb-2 flex items-center gap-1.5 text-blue-400">
                    <CheckCircle className="h-4 w-4" />
                    Structural Observations
                  </h3>
                  <ul className="space-y-3">
                    {analysis.diagnosis.map((d, i) => (
                      <li key={i} className="text-xs text-slate-300 flex items-start gap-2 leading-relaxed">
                        <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Risks list */}
                <div className="rounded-lg border bg-card p-6 space-y-4">
                  <h3 className="font-semibold text-base border-b pb-2 flex items-center gap-1.5 text-red-400">
                    <AlertTriangle className="h-4 w-4" />
                    Identified Vulnerabilities
                  </h3>
                  <ul className="space-y-3">
                    {analysis.risks.map((r, i) => (
                      <li key={i} className="text-xs text-slate-300 flex items-start gap-2 leading-relaxed">
                        <span className="h-1.5 w-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Recommendations Section */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Optimized Pricing Recommendations</h3>
                <p className="text-xs text-muted-foreground -mt-3">
                  These models were simulated deterministically. The AI presents their tradeoffs below.
                </p>

                <div className="grid gap-6 md:grid-cols-3">
                  {analysis.recommendations.map((rec, i) => (
                    <div 
                      key={i} 
                      className={`rounded-lg border bg-card p-6 flex flex-col justify-between gap-5 relative overflow-hidden ${
                        i === 1 ? 'ring-1 ring-blue-500/50 border-blue-500/40' : ''
                      }`}
                    >
                      {i === 1 && (
                        <span className="absolute top-0 right-0 bg-blue-500 text-black text-[9px] uppercase font-bold px-2 py-0.5 rounded-bl">
                          Recommended
                        </span>
                      )}

                      <div className="space-y-4">
                        {/* Title & Setup */}
                        <div>
                          <h4 className="font-bold text-base text-slate-200">{rec.option_name}</h4>
                          <span className="text-[10px] text-muted-foreground block font-medium">
                            ${rec.base_price}/mo • {rec.included_units} tasks • ${rec.overage_price}/task overage
                          </span>
                        </div>

                        {/* Deterministic Stats */}
                        <div className="grid grid-cols-3 gap-1 bg-slate-900/60 border rounded p-2 text-center text-[10px]">
                          <div>
                            <span className="text-muted-foreground block uppercase text-[8px] font-bold">Revenue</span>
                            <span className="font-bold text-slate-200">${(rec.revenue / 1000).toFixed(1)}k</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground block uppercase text-[8px] font-bold">Margin</span>
                            <span className="font-bold text-slate-200">{rec.margin.toFixed(0)}%</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground block uppercase text-[8px] font-bold">Bill Shock</span>
                            <span className="font-bold text-red-400">{rec.high_risk_customers}</span>
                          </div>
                        </div>

                        {/* Tradeoff Explanation */}
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {rec.explanation}
                        </p>
                      </div>

                      <button
                        onClick={() => handleApplyRecommendation(rec)}
                        className={`w-full py-2 rounded text-xs font-semibold transition-colors ${
                          i === 1 
                            ? 'bg-blue-500 text-black hover:bg-blue-400' 
                            : 'border hover:bg-secondary'
                        }`}
                      >
                        Approve & Apply Sliders
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}
        </div>
      )}
    </div>
  );
};
