import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { SimulationResult, FlexpriceDeployment, IngestionStreamLog, IntegrationStatus, ProposedPricing } from '../types';
import { 
  CloudLightning, 
  Play, 
  RefreshCw, 
  Terminal, 
  CheckCircle2, 
  Loader2
} from 'lucide-react';

interface DeploymentsProps {
  simResult: SimulationResult | null;
  proposed: ProposedPricing;
}

export const Deployments: React.FC<DeploymentsProps> = ({ simResult, proposed }) => {
  const [deploying, setDeploying] = useState(false);
  const [deployResult, setDeployResult] = useState<FlexpriceDeployment | null>(null);
  const [deployError, setDeployError] = useState<string | null>(null);
  
  // Status & Event logs
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [streamLogs, setStreamLogs] = useState<IngestionStreamLog[]>([]);
  const [simulatingEvents, setSimulatingEvents] = useState(false);

  const loadStatusAndLogs = async () => {
    try {
      const [statusRes, logsRes] = await Promise.all([
        api.fetchFlexpriceStatus(),
        api.fetchFlexpriceLogs()
      ]);
      setStatus(statusRes);
      setStreamLogs(logsRes);
    } catch (err) {
      console.error("Failed to load status/logs:", err);
    }
  };

  useEffect(() => {
    loadStatusAndLogs();
    
    // Poll logs every 4 seconds to simulate active ingestion stream
    const interval = setInterval(async () => {
      try {
        const logsRes = await api.fetchFlexpriceLogs();
        setStreamLogs(logsRes);
      } catch (e) {}
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const handleDeploy = async () => {
    if (!simResult) return;
    try {
      setDeploying(true);
      setDeployError(null);
      setDeployResult(null);
      const res = await api.deployPricing(simResult.simulation_id);
      setDeployResult(res);
      // Reload stream/status after deploy
      await loadStatusAndLogs();
    } catch (err: any) {
      setDeployError(err.message || 'Deployment execution failed.');
    } finally {
      setDeploying(false);
    }
  };

  const handleGenerateEvents = async () => {
    try {
      setSimulatingEvents(true);
      await api.generateFlexpriceEvents(10);
      const logsRes = await api.fetchFlexpriceLogs();
      setStreamLogs(logsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setSimulatingEvents(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight">Flexprice Deployment</h1>
        <p className="text-sm text-muted-foreground">
          Push approved pricing structures directly toward Flexprice billing engine and simulate event routing.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: Deployment Control */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-lg border bg-card p-6 flex flex-col gap-5">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-semibold text-lg flex items-center gap-1.5">
                <CloudLightning className="h-5 w-5 text-blue-400" />
                Active Configuration Deployer
              </h3>
              {status && (
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${
                  status.mode === 'LIVE' 
                    ? 'bg-green-950/40 text-green-400 border-green-900/40' 
                    : 'bg-amber-950/40 text-amber-400 border-amber-900/40'
                }`}>
                  {status.mode} MODE
                </span>
              )}
            </div>

            {/* Connection configuration summary */}
            {status && (
              <div className="grid grid-cols-2 gap-4 text-xs bg-slate-900/40 p-3 rounded border">
                <div>
                  <span className="text-muted-foreground block text-[9px] uppercase font-bold">Flexprice API Endpoint</span>
                  <span className="font-mono text-slate-200">{status.url}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[9px] uppercase font-bold">Credential Config</span>
                  <span className="font-medium text-slate-200">
                    {status.configured ? 'Active (API Key loaded)' : 'Mocked (Using simulated sandbox)'}
                  </span>
                </div>
              </div>
            )}

            {!simResult ? (
              <div className="rounded border border-dashed p-6 text-center text-xs text-muted-foreground">
                No simulated configuration is active. Go to Revenue Twin and run a simulation before deploying.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground uppercase font-bold">Deploying configuration:</span>
                  <div className="rounded border bg-slate-950 p-3 text-xs">
                    <span className="font-semibold text-slate-200 block font-sans">Proposed Pro Plan Settings</span>
                    <span className="text-muted-foreground">
                      Base Price: ${proposed.base_price}/mo • Included Tasks: {proposed.included_units} • Overage: ${proposed.overage_price.toFixed(2)}/task
                    </span>
                  </div>
                </div>

                {deployError && (
                  <div className="text-xs text-red-400 bg-red-950/20 border border-red-900/30 p-3 rounded">
                    {deployError}
                  </div>
                )}

                <button
                  onClick={handleDeploy}
                  disabled={deploying}
                  className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded bg-white text-black font-semibold text-sm hover:bg-slate-200 transition-colors disabled:bg-slate-800 disabled:text-slate-400"
                >
                  {deploying ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Registering Flexprice Entities...
                    </>
                  ) : (
                    <>
                      <CloudLightning className="h-4 w-4" />
                      Deploy Pricing Configuration
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Deployment Results Timeline logs */}
          {deployResult && (
            <div className="rounded-lg border bg-card p-6 space-y-4 animate-in fade-in duration-300">
              <h3 className="font-semibold text-base border-b pb-2 flex items-center gap-1.5 text-green-400">
                <CheckCircle2 className="h-4 w-4" />
                API Deployment Successful ({deployResult.details.mode} Mode)
              </h3>
              
              <div className="space-y-3.5">
                {deployResult.details.api_call_logs.map((log: any, i: number) => (
                  <div key={i} className="flex gap-3">
                    {/* Circle timeline item */}
                    <div className="flex flex-col items-center">
                      <span className="h-5 w-5 rounded-full bg-slate-900 border border-slate-700 text-[10px] flex items-center justify-center font-bold text-slate-400">
                        {i + 1}
                      </span>
                      {i < deployResult.details.api_call_logs.length - 1 && (
                        <div className="w-0.5 grow bg-slate-800 my-1" />
                      )}
                    </div>

                    {/* Content log detail */}
                    <div className="space-y-1 grow pb-2 text-xs">
                      <div className="flex justify-between items-center font-semibold">
                        <span className="text-slate-200">{log.step}</span>
                        <span className="font-mono text-[9px] text-muted-foreground uppercase">{log.endpoint}</span>
                      </div>
                      <div className="flex justify-between items-center text-[10px] text-muted-foreground">
                        <span>Payload: {JSON.stringify(log.payload)}</span>
                        <span className="text-green-400 font-semibold bg-green-950/20 border border-green-900/30 px-1 rounded">201 CREATED</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column: Event Simulator Stream */}
        <div className="rounded-lg border bg-card p-6 flex flex-col justify-between gap-6 h-[600px]">
          <div className="space-y-4 overflow-hidden flex flex-col grow">
            {/* Simulator Header */}
            <div className="flex items-center justify-between border-b pb-3 shrink-0">
              <div>
                <h3 className="font-semibold text-lg flex items-center gap-1.5">
                  <Terminal className="h-5 w-5 text-muted-foreground" />
                  Live Event Stream
                </h3>
                <span className="text-[10px] text-muted-foreground block">
                  Simulating ResearchPilot API client ingestion events
                </span>
              </div>
              
              <button
                onClick={handleGenerateEvents}
                disabled={simulatingEvents}
                className="p-2 rounded hover:bg-secondary text-muted-foreground hover:text-white transition-colors disabled:text-slate-600"
                title="Inject 10 simulated events"
              >
                {simulatingEvents ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </button>
            </div>

            {/* Event log feed */}
            <div className="space-y-2.5 overflow-y-auto grow pr-1 text-xs font-mono">
              {streamLogs.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground text-xs">
                  Awaiting ingestion logs...
                </div>
              ) : (
                streamLogs.map((log, i) => (
                  <div key={i} className="border bg-slate-950/40 p-2.5 rounded flex flex-col gap-1 hover:border-slate-800 transition-colors">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-slate-400 font-bold">{log.customer_name}</span>
                      <span className="text-muted-foreground">{formatTime(log.timestamp)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-blue-400 text-[10px]">{log.event_name}</span>
                      <span className="text-green-400 text-[9px] bg-green-950/30 border border-green-900/30 px-1 rounded font-bold uppercase">
                        INGESTED
                      </span>
                    </div>
                    <span className="text-muted-foreground text-[10px] truncate">{log.usage}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="border-t pt-4 shrink-0 text-center">
            <button 
              onClick={handleGenerateEvents}
              disabled={simulatingEvents}
              className="w-full flex items-center justify-center gap-1 py-1.5 border rounded text-xs font-semibold hover:bg-secondary transition-colors"
            >
              <RefreshCw className={`h-3 w-3 ${simulatingEvents ? 'animate-spin' : ''}`} />
              Inject Simulated API Workload (+10 Events)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};



function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return ''; }
}
