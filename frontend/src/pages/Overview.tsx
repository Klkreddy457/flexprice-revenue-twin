import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { 
  Users, 
  Cpu, 
  DollarSign, 
  Layers, 
  TrendingUp, 
  ArrowRight,
  Loader2
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

interface OverviewProps {
  onNavigate: (tab: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const res = await api.fetchUsageSummary();
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to load usage summary.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Loading platform intelligence...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-destructive">System Error</h2>
          <p className="text-sm text-muted-foreground">{error || 'Unknown error occurred.'}</p>
        </div>
      </div>
    );
  }

  // Map segments for pie chart
  const segmentData = Object.entries(data.segment_breakdown || {}).map(([name, value]) => ({
    name,
    value
  }));

  const COLORS = ['#94a3b8', '#3b82f6', '#10b981', '#f59e0b'];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header section */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="text-sm text-muted-foreground">
           pricing analytics and server infrastructure utilization for ResearchPilot.
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Total Customers</h3>
            <Users className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-2xl font-bold">1,000</span>
            <span className="text-xs text-muted-foreground">Free, Startup, Growth, Enterprise</span>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Research Tasks Run</h3>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-2xl font-bold">{data.totals.tasks?.toLocaleString() || '100,000+'}</span>
            <span className="text-xs text-muted-foreground">Across last 90 calendar days</span>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Agent Token Usage</h3>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-2xl font-bold">{(data.totals.tokens_used / 1000000).toFixed(1)}M</span>
            <span className="text-xs text-muted-foreground">LLM interactions logged</span>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Default Plan</h3>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-2xl font-bold text-blue-400">Pro Plan</span>
            <span className="text-xs text-muted-foreground">$49/mo, 100 tasks, $0.75 overage</span>
          </div>
        </div>
      </div>

      {/* Hero Simulation Box */}
      <div className="rounded-lg border border-blue-900/30 bg-blue-950/10 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h3 className="font-semibold text-blue-300">Ready to simulate new pricing models?</h3>
          <p className="text-sm text-blue-200/70">
            Run a deterministic simulation of base prices, included usage, and overage structures against your historical dataset of {data.totals.tasks?.toLocaleString()} tasks.
          </p>
        </div>
        <button 
          onClick={() => onNavigate('revenue-twin')}
          className="flex items-center justify-center gap-2 rounded-md bg-white px-4 py-2 text-sm font-medium text-black hover:bg-slate-200 transition-colors shrink-0"
        >
          Open Revenue Twin Laboratory
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Daily usage chart */}
        <div className="md:col-span-2 rounded-lg border bg-card p-6">
          <div className="flex flex-col gap-1 pb-4">
            <h3 className="text-lg font-medium">Daily Platform Utilization</h3>
            <p className="text-xs text-muted-foreground">Daily aggregate of research tasks completed.</p>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.daily_usage}>
                <defs>
                  <linearGradient id="colorTasks" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="tasks" stroke="#3b82f6" fillOpacity={1} fill="url(#colorTasks)" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Customer segments segment distribution */}
        <div className="rounded-lg border bg-card p-6 flex flex-col justify-between">
          <div className="flex flex-col gap-1 pb-2">
            <h3 className="text-lg font-medium">Usage by Segment</h3>
            <p className="text-xs text-muted-foreground">Tasks run across customer tiers.</p>
          </div>
          <div className="h-[230px] flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={segmentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {segmentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs pt-2">
            {segmentData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[index] }} />
                <span className="text-muted-foreground">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
