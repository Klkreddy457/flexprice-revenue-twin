import React, { useState } from 'react';
import { api } from '../services/api';
import type { CustomerImpact, ProposedPricing } from '../types';
import { 
  Search, 
  X, 
  AlertOctagon, 
  Cpu, 
  Database, 
  Clock, 
  BookOpen, 
  Zap, 
  Percent,
  CheckCircle2,
  Loader2
} from 'lucide-react';

interface CustomersProps {
  proposed: ProposedPricing;
  simResult: any; // Accept from RevenueTwin run
}

export const Customers: React.FC<CustomersProps> = ({ proposed, simResult }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [segmentFilter, setSegmentFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerData, setDrawerData] = useState<any>(null);
  const [drawerError, setDrawerError] = useState<string | null>(null);

  // If no simulation was run yet, we fetch details of the last simulation or prompt user
  const impacts: CustomerImpact[] = simResult?.impacts || [];

  const handleOpenDrawer = async (customerId: string) => {
    setDrawerOpen(true);
    setDrawerLoading(true);
    setDrawerError(null);
    try {
      // Pass the current proposed sliders so that the drawer calculates bill details dynamically!
      const res = await api.fetchCustomerDetails(customerId, proposed);
      setDrawerData(res);
    } catch (err: any) {
      setDrawerError(err.message || 'Failed to load customer details.');
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setDrawerData(null);
  };

  // Filter logic
  const filteredImpacts = impacts.filter((imp) => {
    const matchesSearch = imp.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          imp.customer_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSegment = segmentFilter === 'all' || imp.segment.toLowerCase() === segmentFilter.toLowerCase();
    
    let matchesRisk = true;
    if (riskFilter === 'shock') {
      matchesRisk = imp.risk_level === 'HIGH' || imp.risk_level === 'CRITICAL';
    } else if (riskFilter === 'increase') {
      matchesRisk = imp.bill_change > 0.01;
    } else if (riskFilter === 'decrease') {
      matchesRisk = imp.bill_change < -0.01;
    } else if (riskFilter === 'unchanged') {
      matchesRisk = Math.abs(imp.bill_change) <= 0.01;
    }

    return matchesSearch && matchesSegment && matchesRisk;
  });

  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL': return 'bg-red-950/40 text-red-400 border-red-900/50';
      case 'HIGH': return 'bg-orange-950/40 text-orange-400 border-orange-900/50';
      case 'MEDIUM': return 'bg-amber-950/40 text-amber-400 border-amber-900/50';
      default: return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  const getChangeBadgeColor = (change: number) => {
    if (change > 0.01) return 'text-red-400';
    if (change < -0.01) return 'text-green-400';
    return 'text-slate-400';
  };

  return (
    <div className="space-y-6 relative animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight">Customers</h1>
        <p className="text-sm text-muted-foreground">
          Analyze pricing impacts and identify bill shocks across individual accounts.
        </p>
      </div>

      {!simResult ? (
        <div className="rounded-lg border bg-card p-12 text-center flex flex-col items-center justify-center min-h-[350px]">
          <AlertOctagon className="h-10 w-10 text-muted-foreground mb-3" />
          <h3 className="font-semibold text-lg">Simulation Results Required</h3>
          <p className="text-sm text-muted-foreground max-w-md mt-1 mb-4">
            Please run a simulation on the Revenue Twin dashboard first to generate customer impact statistics.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Filters Row */}
          <div className="flex flex-col gap-3 md:flex-row md:items-center justify-between">
            {/* Search Input */}
            <div className="relative max-w-sm w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search customers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded border bg-card pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-slate-500"
              />
            </div>

            {/* Dropdown Filters */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Segment select */}
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-muted-foreground">Segment:</span>
                <select
                  value={segmentFilter}
                  onChange={(e) => setSegmentFilter(e.target.value)}
                  className="rounded border bg-card px-2.5 py-1.5 font-medium cursor-pointer"
                >
                  <option value="all">All Tiers</option>
                  <option value="free">Free</option>
                  <option value="startup">Startup</option>
                  <option value="growth">Growth</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>

              {/* Risk category select */}
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-muted-foreground">Bill Shift:</span>
                <select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  className="rounded border bg-card px-2.5 py-1.5 font-medium cursor-pointer"
                >
                  <option value="all">All Shifts</option>
                  <option value="shock">Bill Shock (&gt;25% Increase)</option>
                  <option value="increase">Bill Increased</option>
                  <option value="decrease">Bill Saved</option>
                  <option value="unchanged">Unchanged</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary banner */}
          <div className="text-xs text-muted-foreground">
            Showing {filteredImpacts.length} of {impacts.length} customers • {impacts.filter(i => i.risk_level === 'HIGH' || i.risk_level === 'CRITICAL').length} at risk of bill shock
          </div>

          {/* Customer Table */}
          <div className="rounded-lg border bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead className="bg-slate-900/60 border-b text-xs uppercase font-semibold text-muted-foreground">
                  <tr>
                    <th className="px-6 py-4">Customer</th>
                    <th className="px-6 py-4">Segment</th>
                    <th className="px-6 py-4 text-right">Current Bill</th>
                    <th className="px-6 py-4 text-right">Proposed Bill</th>
                    <th className="px-6 py-4 text-right">Change</th>
                    <th className="px-6 py-4 text-right">Tasks Run</th>
                    <th className="px-6 py-4 text-right">Est. Margin</th>
                    <th className="px-6 py-4">Risk Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredImpacts.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-12 text-center text-muted-foreground">
                        No customers match the active filter parameters.
                      </td>
                    </tr>
                  ) : (
                    filteredImpacts.map((imp) => (
                      <tr 
                        key={imp.customer_id}
                        onClick={() => handleOpenDrawer(imp.customer_id)}
                        className="hover:bg-slate-900/40 cursor-pointer transition-colors"
                      >
                        <td className="px-6 py-4 font-semibold">
                          <div className="flex flex-col">
                            <span>{imp.customer_name}</span>
                            <span className="text-[10px] text-muted-foreground">{imp.customer_id}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-xs px-2 py-0.5 rounded border bg-slate-900">
                            {imp.segment}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-medium">${imp.current_bill.toFixed(2)}</td>
                        <td className="px-6 py-4 text-right font-medium">${imp.proposed_bill.toFixed(2)}</td>
                        <td className={`px-6 py-4 text-right font-semibold ${getChangeBadgeColor(imp.bill_change)}`}>
                          {imp.bill_change > 0 ? '+' : ''}{imp.bill_change.toFixed(2)}
                          <span className="text-[10px] font-normal block">
                            {imp.bill_change_percent > 0 ? '+' : ''}{imp.bill_change_percent.toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right text-muted-foreground">{imp.usage.toLocaleString()}</td>
                        <td className="px-6 py-4 text-right font-medium">{imp.margin.toFixed(0)}%</td>
                        <td className="px-6 py-4">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${getRiskBadgeColor(imp.risk_level)}`}>
                            {imp.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Sliding Details Drawer Panel */}
      {drawerOpen && (
        <>
          {/* Overlay backdrop */}
          <div 
            onClick={handleCloseDrawer}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
          />

          {/* Drawer body */}
          <div className="fixed right-0 top-0 bottom-0 w-full max-w-lg bg-card border-l z-50 shadow-2xl p-6 overflow-y-auto animate-in slide-in-from-right duration-300 flex flex-col justify-between">
            <div>
              {/* Drawer Header */}
              <div className="flex items-center justify-between border-b pb-4 mb-6">
                <div>
                  <h3 className="text-lg font-bold">Account Overview</h3>
                  <span className="text-xs text-muted-foreground">Detailed usage & bill analysis</span>
                </div>
                <button 
                  onClick={handleCloseDrawer}
                  className="rounded-full p-1.5 hover:bg-secondary text-muted-foreground hover:text-white transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {drawerLoading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-2">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground font-medium">Aggregating account logs...</span>
                </div>
              ) : drawerError ? (
                <div className="text-center py-12 text-destructive">
                  <p>{drawerError}</p>
                </div>
              ) : drawerData ? (
                <div className="space-y-6">
                  {/* Account Name Banner */}
                  <div className="flex flex-col gap-1">
                    <h2 className="text-2xl font-bold">{drawerData.customer.name}</h2>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-muted-foreground">{drawerData.customer.id}</span>
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-700" />
                      <span className="text-muted-foreground">{drawerData.customer.segment} Segment</span>
                    </div>
                  </div>

                  {/* Pricing Comparison Cards */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-slate-900/60 border rounded-lg p-3 text-center">
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold">Current Bill</span>
                      <div className="text-lg font-bold">${drawerData.totals.current_bill.toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-900/60 border rounded-lg p-3 text-center">
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold">Proposed Bill</span>
                      <div className="text-lg font-bold">${drawerData.totals.proposed_bill.toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-900/60 border rounded-lg p-3 text-center">
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold">Bill Shift</span>
                      <div className={`text-lg font-bold ${
                        drawerData.totals.bill_change > 0.01 ? 'text-red-400' : drawerData.totals.bill_change < -0.01 ? 'text-green-400' : 'text-slate-400'
                      }`}>
                        {drawerData.totals.bill_change > 0 ? '+' : ''}${drawerData.totals.bill_change.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {/* Why did it change? box */}
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                    <h4 className="text-xs text-muted-foreground uppercase font-bold mb-1.5 flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                      Numerical Root Cause
                    </h4>
                    <p className="text-xs leading-relaxed text-slate-300">
                      {drawerData.change_explanation}
                    </p>
                  </div>

                  {/* Infrastructure Cost & Margin details */}
                  <div className="grid grid-cols-2 gap-4 border-t pt-4">
                    <div>
                      <span className="text-xs text-muted-foreground block">Infrastructure Cost</span>
                      <span className="text-lg font-bold">${drawerData.totals.infra_cost.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground block">Proposed Gross Margin</span>
                      <span className="text-lg font-bold">{drawerData.totals.margin.toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Usage Breakdown */}
                  <div className="space-y-3 border-t pt-4">
                    <h4 className="text-xs text-muted-foreground uppercase font-bold">90-Day Raw Usage Metrics</h4>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {/* Metric 1 */}
                      <div className="flex items-center gap-2 border bg-slate-950/40 p-2.5 rounded">
                        <BookOpen className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Research Tasks</span>
                          <span className="font-bold">{drawerData.totals.tasks.toLocaleString()}</span>
                        </div>
                      </div>

                      {/* Metric 2 */}
                      <div className="flex items-center gap-2 border bg-slate-950/40 p-2.5 rounded">
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Agent Calls</span>
                          <span className="font-bold">{drawerData.totals.agent_calls.toLocaleString()}</span>
                        </div>
                      </div>

                      {/* Metric 3 */}
                      <div className="flex items-center gap-2 border bg-slate-950/40 p-2.5 rounded">
                        <Database className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Tokens Transacted</span>
                          <span className="font-bold">{(drawerData.totals.tokens_used / 1000).toFixed(0)}k</span>
                        </div>
                      </div>

                      {/* Metric 4 */}
                      <div className="flex items-center gap-2 border bg-slate-950/40 p-2.5 rounded">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Compute Seconds</span>
                          <span className="font-bold">{drawerData.totals.compute_seconds.toLocaleString()}s</span>
                        </div>
                      </div>

                      {/* Metric 5 */}
                      <div className="flex items-center gap-2 border bg-slate-950/40 p-2.5 rounded">
                        <Zap className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Premium Models</span>
                          <span className="font-bold">{drawerData.totals.premium_model_calls.toLocaleString()}</span>
                        </div>
                      </div>

                      {/* Metric 6 */}
                      <div className="flex items-center gap-2 border bg-slate-950/40 p-2.5 rounded">
                        <Percent className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Documents Loaded</span>
                          <span className="font-bold">{drawerData.totals.documents_processed.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Monthly Trend list */}
                  <div className="space-y-3 border-t pt-4">
                    <h4 className="text-xs text-muted-foreground uppercase font-bold">Monthly Usage Trend</h4>
                    <div className="space-y-1.5">
                      {drawerData.monthly_details.map((m: any) => (
                        <div key={m.month} className="flex items-center justify-between text-xs border bg-slate-950/20 px-3 py-2 rounded">
                          <span className="font-semibold">{m.month}</span>
                          <span className="text-muted-foreground">{m.tasks} tasks run</span>
                          <span className="font-medium">${m.proposed_bill.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            <div className="border-t pt-4 mt-6">
              <button 
                onClick={handleCloseDrawer}
                className="w-full py-2 border rounded font-semibold text-sm hover:bg-secondary transition-colors"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
