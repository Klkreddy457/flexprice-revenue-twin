import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import type { SimulationResult, ProposedPricing, IntegrationStatus } from './types';
import { Overview } from './pages/Overview';
import { RevenueTwin } from './pages/RevenueTwin';
import { Customers } from './pages/Customers';
import { AIDoctor } from './pages/AIDoctor';
import { Deployments } from './pages/Deployments';
import { 
  Workflow, 
  Users, 
  Cpu, 
  Sparkles, 
  CloudLightning, 
  LayoutDashboard, 
  Loader2,
  Info
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('revenue-twin');
  const [proposed, setProposed] = useState<ProposedPricing>({
    base_price: 49,
    included_units: 100,
    overage_price: 0.75,
    pricing_metric: 'research_tasks'
  });
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [integration, setIntegration] = useState<IntegrationStatus | null>(null);
  const [initializing, setInitializing] = useState(true);

  const triggerSimulation = async (pricing: ProposedPricing) => {
    try {
      const result = await api.runSimulation('pm_pro_default', pricing);
      setSimResult(result);
    } catch (e) {
      console.error("Simulation run failed:", e);
    }
  };

  useEffect(() => {
    async function initPlatform() {
      try {
        setInitializing(true);
        // Fetch last simulation or trigger initial run
        const [sim, status] = await Promise.all([
          api.fetchLastSimulation(),
          api.fetchFlexpriceStatus()
        ]);
        setSimResult(sim);
        setIntegration(status);
        
        // Match state to last simulation values if available
        if (sim && (sim as any).proposed_pricing_data) {
          const propData = (sim as any).proposed_pricing_data;
          setProposed({
            base_price: propData.base_price || 49,
            included_units: propData.included_units || 100,
            overage_price: propData.overage_price || 0.75,
            pricing_metric: propData.pricing_metric || 'research_tasks'
          });
        }
      } catch (err) {
        console.error("Initialization failed:", err);
      } finally {
        setInitializing(false);
      }
    }
    initPlatform();
  }, []);

  if (initializing) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
          <h2 className="text-lg font-bold tracking-tight">Flexprice Revenue Twin</h2>
          <span className="text-xs text-muted-foreground">Bootstrapping simulation environment...</span>
        </div>
      </div>
    );
  }

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'revenue-twin', label: 'Revenue Twin', icon: Workflow },
    { id: 'customers', label: 'Customers', icon: Users },
    { id: 'ai-doctor', label: 'AI Pricing Doctor', icon: Sparkles },
    { id: 'deployments', label: 'Flexprice Deployment', icon: CloudLightning }
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r bg-card flex flex-col justify-between shrink-0">
        <div className="flex flex-col">
          {/* Brand Header */}
          <div className="h-16 border-b px-6 flex items-center gap-2">
            <div className="h-7 w-7 rounded bg-white flex items-center justify-center text-black font-extrabold text-sm tracking-tighter">
              FP
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight leading-none text-slate-100">Flexprice</span>
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider mt-0.5">Revenue Twin</span>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="p-4 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded text-sm font-semibold transition-colors ${
                    isActive 
                      ? 'bg-slate-900 text-white' 
                      : 'text-muted-foreground hover:text-white hover:bg-slate-900/40'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-blue-400' : ''}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer Demo Profile */}
        <div className="border-t p-4 bg-slate-900/20">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-slate-800 border flex items-center justify-center text-[10px] font-bold text-slate-400">
              RP
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-bold text-slate-200 truncate">ResearchPilot</span>
              <span className="text-[9px] text-muted-foreground truncate">AI Research Agent Platform</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Panel Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar header */}
        <header className="h-16 border-b bg-card px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold text-muted-foreground">Tenant:</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded bg-secondary text-slate-200 border">
              ResearchPilot Inc.
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            {integration && (
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground">Billing:</span>
                <span className={`h-2 w-2 rounded-full pulse-green ${
                  integration.mode === 'LIVE' ? 'bg-green-500' : 'bg-amber-400'
                }`} />
                <span className="font-semibold text-slate-200">
                  {integration.mode === 'LIVE' ? 'Live Flexprice Mode' : 'Demo Sandbox Mode'}
                </span>
              </div>
            )}
            
            {simResult && (
              <div className="text-muted-foreground flex items-center gap-1 border-l pl-4 border-slate-800">
                <Info className="h-3.5 w-3.5" />
                <span>Simulated deterministic models loaded</span>
              </div>
            )}
          </div>
        </header>

        {/* Page Content Panel */}
        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'overview' && (
            <Overview onNavigate={setActiveTab} />
          )}
          {activeTab === 'revenue-twin' && (
            <RevenueTwin 
              proposed={proposed} 
              setProposed={setProposed} 
              simResult={simResult} 
              setSimResult={setSimResult} 
              onNavigate={setActiveTab} 
            />
          )}
          {activeTab === 'customers' && (
            <Customers 
              proposed={proposed} 
              simResult={simResult} 
            />
          )}
          {activeTab === 'ai-doctor' && (
            <AIDoctor 
              simResult={simResult} 
              setProposed={setProposed} 
              onNavigate={setActiveTab} 
              triggerSimulation={triggerSimulation}
            />
          )}
          {activeTab === 'deployments' && (
            <Deployments 
              simResult={simResult} 
              proposed={proposed}
            />
          )}
        </div>
      </main>
    </div>
  );
};
export default App;
