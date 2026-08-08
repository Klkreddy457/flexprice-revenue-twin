import React, { useState } from 'react';
import { api } from '../services/api';
import type { SimulationResult, ProposedPricing } from '../types';
import { 
  TrendingDown, 
  TrendingUp, 
  AlertTriangle,
  Heart,
  Loader2,
  RefreshCw,
  Info,
  ChevronRight
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface RevenueTwinProps {
  proposed: ProposedPricing;
  setProposed: React.Dispatch<React.SetStateAction<ProposedPricing>>;
  simResult: SimulationResult | null;
  setSimResult: React.Dispatch<React.SetStateAction<SimulationResult | null>>;
  onNavigate: (tab: string) => void;
}

type ProjectionPeriod = 'monthly' | 'quarterly' | 'annualized';

export const RevenueTwin: React.FC<RevenueTwinProps> = ({ 
  proposed, 
  setProposed, 
  simResult, 
  setSimResult,
  onNavigate
}) => {
  const [simulating, setSimulating] = useState(false);
  const [projectionPeriod, setProjectionPeriod] = useState<ProjectionPeriod>('monthly');
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = async () => {
    try {
      setSimulating(true);
      setError(null);
      // "pm_pro_default" is the seeded current pricing model
      const result = await api.runSimulation('pm_pro_default', proposed);
      setSimResult(result);
    } catch (err: any) {
      setError(err.message || 'Simulation execution failed.');
    } finally {
      setSimulating(false);
    }
  };

  const getProjectionMultiplier = (): number => {
    if (projectionPeriod === 'quarterly') return 3;
    if (projectionPeriod === 'annualized') return 12;
    return 1;
  };

  const formatPeriodLabel = (val: string) => {
    if (projectionPeriod === 'quarterly') return `${val} (Quarter)`;
    if (projectionPeriod === 'annualized') return `${val} (Annual)`;
    return `${val} (Month)`;
  };

  // Setup data for bar chart
  const mult = getProjectionMultiplier();
  const chartData = simResult ? [
    {
      name: 'Revenue',
      Current: simResult.revenue.current * mult,
      Proposed: simResult.revenue.proposed * mult
    },
    {
      name: 'Infrastructure Cost',
      Current: simResult.cost.current * mult,
      Proposed: simResult.cost.proposed * mult
    }
  ] : [];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col gap-1 md:flex-row md:items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Revenue Twin</h1>
          <p className="text-sm text-muted-foreground">
            Simulate your pricing before your customers experience it.
          </p>
        </div>
        
        {simResult && (
          <span className="text-xs text-muted-foreground flex items-center gap-1 bg-slate-900 border px-2 py-1 rounded-md">
            <Info className="h-3 w-3" />
            Last simulation: Active model pm_pro_default comparison
          </span>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Sliders Control Panel */}
        <div className="lg:col-span-2 rounded-lg border bg-card p-6 flex flex-col gap-6 h-fit">
          <div className="flex items-center justify-between border-b pb-4">
            <h3 className="font-semibold text-lg">Proposed Pricing</h3>
            <button 
              onClick={handleSimulate} 
              disabled={simulating}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white text-black font-medium text-xs hover:bg-slate-200 disabled:bg-slate-800 disabled:text-slate-400 transition-colors"
            >
              {simulating ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Simulating...
                </>
              ) : (
                <>
                  <RefreshCw className="h-3.5 w-3.5" />
                  Simulate Pricing
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="text-xs text-red-400 bg-red-950/20 border border-red-900/30 p-3 rounded">
              {error}
            </div>
          )}

          {/* Slider 1: Base Price */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <label className="text-muted-foreground font-medium">Base Subscription Fee</label>
              <span className="font-semibold">${proposed.base_price}/mo</span>
            </div>
            <input 
              type="range" 
              min="10" 
              max="500" 
              step="1"
              value={proposed.base_price}
              onChange={(e) => setProposed({ ...proposed, base_price: Number(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>$10</span>
              <span>$250</span>
              <span>$500</span>
            </div>
          </div>

          {/* Slider 2: Included Units */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <label className="text-muted-foreground font-medium">Included Research Tasks</label>
              <span className="font-semibold">{proposed.included_units} tasks/mo</span>
            </div>
            <input 
              type="range" 
              min="10" 
              max="1000" 
              step="5"
              value={proposed.included_units}
              onChange={(e) => setProposed({ ...proposed, included_units: Number(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>10</span>
              <span>500</span>
              <span>1,000</span>
            </div>
          </div>

          {/* Slider 3: Overage price */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <label className="text-muted-foreground font-medium">Overage Rate (Per Task)</label>
              <span className="font-semibold">${proposed.overage_price.toFixed(2)}</span>
            </div>
            <input 
              type="range" 
              min="0.10" 
              max="5.00" 
              step="0.05"
              value={proposed.overage_price}
              onChange={(e) => setProposed({ ...proposed, overage_price: Number(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>$0.10</span>
              <span>$2.50</span>
              <span>$5.00</span>
            </div>
          </div>

          {/* Static Pricing Metric */}
          <div className="space-y-2 pt-2 border-t">
            <label className="text-xs text-muted-foreground uppercase font-semibold">Pricing Metric</label>
            <div className="rounded border bg-slate-900/50 px-3 py-2 text-sm font-medium">
              research_tasks (events: research_completed)
            </div>
          </div>
        </div>

        {/* Right Pane: Executive results summary */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          {!simResult ? (
            <div className="rounded-lg border bg-card p-6 flex flex-col items-center justify-center text-center grow min-h-[300px]">
              <AlertTriangle className="h-8 w-8 text-muted-foreground mb-2" />
              <h3 className="font-semibold text-lg">No Active Simulation</h3>
              <p className="text-sm text-muted-foreground max-w-sm mb-4">
                Adjust the pricing parameters on the left and click Simulate to evaluate model change behavior.
              </p>
              <button 
                onClick={handleSimulate}
                className="px-4 py-2 rounded bg-white text-black font-semibold text-sm hover:bg-slate-200 transition-colors"
              >
                Run Default Simulation
              </button>
            </div>
          ) : (
            <>
              {/* Executive Cards */}
              <div className="grid gap-4 md:grid-cols-2 grow">
                {/* Revenue Card */}
                <div className="rounded-lg border bg-card p-6 flex flex-col justify-between">
                  <div className="flex justify-between items-start pb-2">
                    <span className="text-xs text-muted-foreground uppercase font-semibold">Gross Revenue</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold flex items-center gap-0.5 ${
                      simResult.revenue.change_percent >= 0 
                        ? 'bg-green-950/30 text-green-400 border border-green-900/40' 
                        : 'bg-red-950/30 text-red-400 border border-red-900/40'
                    }`}>
                      {simResult.revenue.change_percent >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {simResult.revenue.change_percent >= 0 ? '+' : ''}{simResult.revenue.change_percent}%
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold flex items-baseline gap-2">
                      ${(simResult.revenue.proposed / 1000).toFixed(1)}k
                      <span className="text-sm text-muted-foreground font-normal">
                        from ${(simResult.revenue.current / 1000).toFixed(1)}k
                      </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                      {simResult.revenue.change >= 0 ? 'Expansion of' : 'Leaked'} ${Math.abs(simResult.revenue.change).toLocaleString()} over 90 days
                    </div>
                  </div>
                </div>

                {/* Gross Margin Card */}
                <div className="rounded-lg border bg-card p-6 flex flex-col justify-between">
                  <div className="flex justify-between items-start pb-2">
                    <span className="text-xs text-muted-foreground uppercase font-semibold">Gross Margin</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                      simResult.margin.change_pp >= 0 
                        ? 'bg-green-950/30 text-green-400 border border-green-900/40' 
                        : 'bg-red-950/30 text-red-400 border border-red-900/40'
                    }`}>
                      {simResult.margin.change_pp >= 0 ? '+' : ''}{simResult.margin.change_pp.toFixed(1)} pp
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold flex items-baseline gap-2">
                      {simResult.margin.proposed.toFixed(1)}%
                      <span className="text-sm text-muted-foreground font-normal">
                        from {simResult.margin.current.toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                      Compute infrastructure costs absorb {((simResult.cost.proposed / simResult.revenue.proposed) * 100).toFixed(1)}% of income
                    </div>
                  </div>
                </div>

                {/* Customer Volatility Card */}
                <div className="rounded-lg border bg-card p-6 flex flex-col justify-between">
                  <div className="flex justify-between items-start pb-2">
                    <span className="text-xs text-muted-foreground uppercase font-semibold">Affected Accounts</span>
                    <span className="text-xs text-muted-foreground bg-slate-900 border px-2 py-0.5 rounded">
                      {simResult.customers.affected} bills shifted
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold flex items-baseline gap-2">
                      {simResult.customers.high_risk} High Risk
                    </div>
                    <div className="text-[10px] text-red-400 mt-1 flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" />
                      {simResult.customers.high_risk} accounts experience bill shock &gt;25%
                    </div>
                  </div>
                </div>

                {/* Pricing Health Card */}
                <div className="rounded-lg border bg-card p-6 flex flex-col justify-between">
                  <div className="flex justify-between items-start pb-2">
                    <span className="text-xs text-muted-foreground uppercase font-semibold">Pricing Health</span>
                    <span className="text-xs text-blue-400 bg-blue-950/30 border border-blue-900/40 px-2 py-0.5 rounded-full font-semibold flex items-center gap-0.5">
                      <Heart className="h-3 w-3 fill-blue-400" />
                      Deterministic
                    </span>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {simResult.health_score.overall.toFixed(0)} / 100
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                      Margin: {simResult.health_score.margin.toFixed(0)} • Risk: {simResult.health_score.predictability.toFixed(0)} • Align: {simResult.health_score.usage_alignment.toFixed(0)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick links to actions */}
              <div className="grid gap-2 grid-cols-3">
                <button 
                  onClick={() => onNavigate('customers')}
                  className="rounded border p-3 text-left hover:bg-slate-900/50 transition-colors flex items-center justify-between"
                >
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold">Analyze Customers</span>
                    <span className="text-[10px] text-muted-foreground">View bill shock reports</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </button>
                <button 
                  onClick={() => onNavigate('ai-doctor')}
                  className="rounded border p-3 text-left hover:bg-slate-900/50 transition-colors flex items-center justify-between"
                >
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold">Consult AI Doctor</span>
                    <span className="text-[10px] text-muted-foreground">Diagnose leaks & optimize</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </button>
                <button 
                  onClick={() => onNavigate('deployments')}
                  className="rounded border p-3 text-left hover:bg-slate-900/50 transition-colors flex items-center justify-between"
                >
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold">Deploy to Flexprice</span>
                    <span className="text-[10px] text-muted-foreground">Sync billing configuration</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {simResult && (
        <div className="grid gap-6 md:grid-cols-3">
          {/* Projections chart */}
          <div className="md:col-span-2 rounded-lg border bg-card p-6">
            <div className="flex items-center justify-between pb-4">
              <div className="flex flex-col gap-1">
                <h3 className="text-lg font-medium">Pricing Projections</h3>
                <p className="text-xs text-muted-foreground">Revenue and cost outlook comparison.</p>
              </div>
              <div className="flex rounded border bg-slate-950 p-0.5 text-xs">
                {(['monthly', 'quarterly', 'annualized'] as ProjectionPeriod[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setProjectionPeriod(p)}
                    className={`px-2 py-1 rounded transition-colors capitalize ${
                      projectionPeriod === p ? 'bg-white text-black font-semibold' : 'text-muted-foreground hover:text-white'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(value: any, name: any) => [`$${Number(value).toLocaleString()}`, formatPeriodLabel(name)]}
                  />
                  <Legend verticalAlign="top" height={36} iconType="circle" />
                  <Bar dataKey="Current" fill="#475569" radius={[4, 4, 0, 0]} maxBarSize={50} />
                  <Bar dataKey="Proposed" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={50} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pricing Health scorecard breaking down deterministic rules */}
          <div className="rounded-lg border bg-card p-6 flex flex-col justify-between">
            <div className="flex flex-col gap-1 pb-4">
              <h3 className="text-lg font-medium">Pricing Health Breakdown</h3>
              <p className="text-xs text-muted-foreground">Deterministic scores of the proposed plan.</p>
            </div>
            
            <div className="space-y-3.5 grow flex flex-col justify-center">
              {/* Score 1 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Margin Health</span>
                  <span className="text-muted-foreground">{simResult.health_score.margin.toFixed(0)}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${simResult.health_score.margin}%` }} />
                </div>
              </div>

              {/* Score 2 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Customer Predictability (Low Bill Shock)</span>
                  <span className="text-muted-foreground">{simResult.health_score.predictability.toFixed(0)}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: `${simResult.health_score.predictability}%` }} />
                </div>
              </div>

              {/* Score 3 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Usage Alignment</span>
                  <span className="text-muted-foreground">{simResult.health_score.usage_alignment.toFixed(0)}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${simResult.health_score.usage_alignment}%` }} />
                </div>
              </div>

              {/* Score 4 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Heavy User Risk (Uncapped Coverage)</span>
                  <span className="text-muted-foreground">{simResult.health_score.heavy_user_risk.toFixed(0)}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: `${simResult.health_score.heavy_user_risk}%` }} />
                </div>
              </div>

              {/* Score 5 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Revenue Efficiency</span>
                  <span className="text-muted-foreground">{simResult.health_score.revenue_efficiency.toFixed(0)}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: `${simResult.health_score.revenue_efficiency}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
