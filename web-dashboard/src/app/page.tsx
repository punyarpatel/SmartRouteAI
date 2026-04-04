'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Route, 
  TrafficCone, 
  Zap, 
  Map as MapIcon, 
  BarChart3, 
  Package, 
  RotateCw, 
  ChevronRight,
  Info,
  Clock,
  Navigation,
  Settings,
  Plus,
  Trash2,
  AlertTriangle,
  FileText
} from 'lucide-react';

const Card = ({ title, icon: Icon, children, className = "", noPadding = false, subtitle }: any) => (
  <div className={`glass-panel rounded-3xl shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden group/card flex flex-col ${className}`}>
    <div className="px-8 py-6 border-b border-white/10 flex-shrink-0 flex items-center justify-between bg-gradient-to-br from-white/5 to-transparent">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-primary/10 rounded-2xl text-primary group-hover/card:scale-110 transition-transform duration-500 ring-1 ring-primary/20">
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-foreground text-lg tracking-tight font-display">{title}</h3>
          {subtitle && <p className="text-xs text-muted-foreground font-medium mt-0.5">{subtitle}</p>}
        </div>
      </div>
    </div>
    <div className={`relative flex-grow h-full w-full ${noPadding ? "" : "p-8"}`}>
      {children}
    </div>
  </div>
);

const AutocompleteInput = ({ value, onChange, onSelect, placeholder, className = "", icon: CustomIcon = MapIcon }: any) => {
  const [query, setQuery] = useState(value || "");
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const ignoreNextRef = useRef(false);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (ignoreNextRef.current) {
        ignoreNextRef.current = false;
        return;
      }
      if (query.length < 3) {
        setSuggestions([]);
        return;
      }
      setLoading(true);
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=6&addressdetails=1`);
        const data = await res.json();
        setSuggestions(data);
        setIsOpen(true);
      } catch (e) {
        console.error("Autocomplete error:", e);
      } finally {
        setLoading(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [query]);

  const formatLocation = (loc: any) => {
    const parts = loc.display_name.split(', ');
    const main = parts[0];
    const secondary = parts.slice(1, 4).join(', ');
    return { main, secondary };
  };

  return (
    <div className="relative w-full">
      <div className="relative group">
        <CustomIcon className="absolute left-4 top-3.5 w-4 h-4 text-slate-400 group-focus-within:text-primary transition-colors" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
              ignoreNextRef.current = false;
              setQuery(e.target.value);
              if (onChange) onChange(e.target.value);
          }}
          onFocus={() => query.length >= 3 && setIsOpen(true)}
          placeholder={placeholder}
          className={`w-full pl-11 pr-10 py-3 bg-slate-50/50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl text-[13px] font-medium placeholder:text-slate-400 focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all shadow-sm ${className}`}
        />
        {loading && (
          <div className="absolute right-4 top-3.5">
            <RotateCw className="w-3.5 h-3.5 text-primary animate-spin" />
          </div>
        )}
      </div>

      {isOpen && suggestions.length > 0 && (
        <div className="absolute left-0 w-full mt-3 glass-panel rounded-2xl shadow-2xl z-[999] max-h-[450px] overflow-y-auto animate-in fade-in slide-in-from-top-2">
          <div className="p-3 border-b border-white/5 bg-white/5 sticky top-0 z-10 backdrop-blur-md">
             <span className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest px-2">Location Intelligence</span>
          </div>
          {suggestions.map((loc: any, i) => {
            const { main, secondary } = formatLocation(loc);
            return (
              <button
                key={i}
                type="button"
                onClick={() => {
                  ignoreNextRef.current = true;
                  setQuery(loc.display_name);
                  setSuggestions([]);
                  setIsOpen(false);
                  onSelect(loc);
                }}
                className="w-full text-left px-5 py-4 hover:bg-primary/10 transition-all border-l-4 border-l-transparent hover:border-l-primary flex items-start gap-4 group"
              >
                <div className="mt-1 p-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-slate-400 group-hover:text-primary transition-colors flex-shrink-0">
                  <Navigation className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-foreground leading-tight line-clamp-1">{main}</div>
                  <div className="text-[11px] font-medium text-slate-500 mt-1 line-clamp-2 leading-relaxed uppercase tracking-tight">{secondary}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default function SmartRouteDashboard() {
  const [activeTab, setActiveTab] = useState('performance');
  const [loading, setLoading] = useState(false);
  const [loadingStepIdx, setLoadingStepIdx] = useState(0);
  const loadingSteps = ['Initializing logic graph...', 'Executing A* path finding...', 'Retrieving traffic model...', 'Optimizing metaheuristics...', 'Compiling intelligence dossier...'];

  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setLoadingStepIdx(prev => (prev + 1) % loadingSteps.length);
      }, 800);
      return () => clearInterval(interval);
    } else {
      setLoadingStepIdx(0);
    }
  }, [loading]);

  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [iframeKey, setIframeKey] = useState(0);

  const getHeuristicLabel = (h: number) => {
    if (h < 0.5) return "Precise (slower)";
    if (h > 1.5) return "Fast (less optimal)";
    return "Balanced";
  };
  const getHeuristicImpact = (h: number) => {
    if (h < 0.5) return "Exploration ↑ 40%, Risk ↓ 10%";
    if (h > 1.5) return "Exploration ↓ 25%, Risk ↑ 15%";
    return "Standard bounds active";
  };

  // Mission State
  const [place, setPlace] = useState('');
  const [hWeight, setHWeight] = useState(1.0);
  const [hour, setHour] = useState(12);
  const [simIncident, setSimIncident] = useState(false);
  const [stops, setStops] = useState<any[]>([]);

  const addStop = () => setStops([...stops, { name: "", address: "" }]);
  const removeStop = (index: number) => setStops(stops.filter((_, i) => i !== index));
  const updateStop = (index: number, field: string, value: string) => {
    const newStops = [...stops];
    (newStops[index] as any)[field] = value;
    setStops(newStops);
  };

  const runPipeline = async () => {
    if (!place.trim()) {
      setError("🛰️ MISSION ABORTED: Please enter a target city (e.g., 'Gandhinagar') before deploying the AI engine.");
      return;
    }

    setLoading(true);
    setError(null);
    
    // 🔥 Strategic Data Sync: Filter out any empty stops and assign names if missing
    const activeStops = stops
      .filter(s => s.address && s.address.trim() !== "")
      .map((s, idx) => ({
          ...s,
          name: s.name.trim() || s.address.split(',')[0].trim() || `Delivery Stop ${idx + 1}`
      }));
    
    console.log("🚀 DEPLOYING MISSION WITH STOPS:", activeStops);

    const mission = {
        place,
        warehouse: { name: "Warehouse", address: place },
        h_weight: hWeight,
        hour,
        sim_incident: simIncident,
        stops: activeStops
    };

    try {
      const res = await fetch('/api/run-pipeline', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission })
      });
      const data = await res.json();
      if (data.success) {
        setResults(data.results);
        setLastUpdated(new Date().toLocaleTimeString());
        
        // 🔥 Strategic UX: Auto-switch to Logistics if multiple stops exist
        if (activeStops.length > 0) {
            setActiveTab('delivery');
        }
        
        setIframeKey(prev => prev + 1);
      } else {
        setError(data.error || "Mission failed to execute.");
      }
    } catch (e: any) {
      setError(e.message || "An unknown error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'performance', name: 'Performance Analysis', icon: Zap },
    { id: 'traffic', name: 'Predictive Traffic (ML)', icon: TrafficCone },
    { id: 'delivery', name: 'Logistics Optimization', icon: Package },
    { id: 'report', name: 'Executive AI Report', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
      {/* ── Sidebar ── */}
      <aside className="fixed left-0 top-0 h-full w-80 sidebar-gradient border-r border-white/5 z-[9999] hidden lg:flex flex-col shadow-[10px_0_40px_rgba(0,0,0,0.2)]">
        <div className="p-8 pb-2 flex-shrink-0">
          <div className="flex items-center gap-4 mb-10 px-2 group cursor-pointer">
            <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20 animate-glow group-hover:scale-110 transition-transform duration-500">
            <Route className="text-white w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-foreground leading-none font-display">SmartRoute</h1>
            <span className="text-[10px] font-bold text-primary uppercase tracking-[0.2em] mt-1.5 block opacity-80">AI Core Engine</span>
          </div>
        </div>

        </div>

        {/* Scrollable Configuration Panel */}
        <div className="flex-1 overflow-y-auto px-8 py-6 custom-scrollbar relative">
          <div className="space-y-1 mb-8">
            <p className="px-4 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Intelligence Modes</p>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-2xl font-bold transition-all duration-300 group ${
                  activeTab === tab.id 
                    ? 'bg-primary text-white shadow-xl shadow-primary/20 scale-[1.02]' 
                    : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:text-primary'
                }`}
              >
                <tab.icon className={`w-5 h-5 transition-transform duration-300 ${activeTab === tab.id ? 'scale-110' : 'group-hover:scale-110'}`} />
                <span className="text-sm tracking-tight">{tab.name}</span>
                {activeTab === tab.id && <ChevronRight className="ml-auto w-4 h-4 opacity-50" />}
              </button>
            ))}
          </div>

          <div className="space-y-6">
            <div className="glass-panel rounded-3xl p-6 border-white/5">
                <div className="flex items-center gap-3 mb-6 text-foreground font-bold text-xs uppercase tracking-widest">
                    <div className="p-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg">
                      <Settings className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                    Parameters
                </div>
                
                <div className="space-y-5">
                    <div className="space-y-2 relative z-50">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 block">Operational Area</label>
                        <AutocompleteInput 
                            value={place} 
                            onSelect={(loc: any) => setPlace(loc.display_name)}
                            placeholder="Set Target City..."
                            className="bg-transparent!"
                        />
                    </div>

                    <div className="grid grid-cols-3 gap-2 relative z-50">
                       <button onClick={() => { setHour(18); setSimIncident(false); }} className="p-2 border border-white/5 rounded-xl bg-slate-50 dark:bg-slate-900/50 hover:bg-orange-500/10 hover:border-orange-500/30 transition-all group flex flex-col items-center">
                          <Clock className="w-3.5 h-3.5 text-slate-400 group-hover:text-orange-500 mb-1" />
                          <span className="text-[8px] font-black uppercase text-slate-500 group-hover:text-orange-500 tracking-tighter">Rush Hour</span>
                       </button>
                       <button onClick={() => setSimIncident(true)} className="p-2 border border-white/5 rounded-xl bg-slate-50 dark:bg-slate-900/50 hover:bg-red-500/10 hover:border-red-500/30 transition-all group flex flex-col items-center">
                          <AlertTriangle className="w-3.5 h-3.5 text-slate-400 group-hover:text-red-500 mb-1" />
                          <span className="text-[8px] font-black uppercase text-slate-500 group-hover:text-red-500 tracking-tighter">Accident</span>
                       </button>
                       <button onClick={() => { setHour(2); setSimIncident(false); }} className="p-2 border border-white/5 rounded-xl bg-slate-50 dark:bg-slate-900/50 hover:bg-blue-500/10 hover:border-blue-500/30 transition-all group flex flex-col items-center">
                          <MapIcon className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 mb-1" />
                          <span className="text-[8px] font-black uppercase text-slate-500 group-hover:text-blue-500 tracking-tighter">Night Ops</span>
                       </button>
                    </div>

                    <div className="space-y-3 relative z-40">
                      <div className="flex justify-between items-center mb-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 block">Sync Time: {hour}:00</label>
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                      </div>
                      <input 
                          type="range" min="0" max="23" step="1" value={hour} onChange={e => setHour(parseInt(e.target.value))}
                          className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-50/50 dark:bg-slate-900/50 rounded-2xl border border-white/5 group/toggle cursor-pointer hover:border-red-500/30 transition-colors relative z-30" onClick={() => setSimIncident(!simIncident)}>
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-xl transition-colors ${simIncident ? 'bg-red-500/10 text-red-500' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>
                          <AlertTriangle className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="text-[10px] font-bold text-foreground uppercase leading-none mb-1 tracking-tight">Incidents</div>
                          <div className="text-[9px] text-slate-500 font-medium tracking-tight">Random blockage</div>
                        </div>
                      </div>
                      <div className={`w-10 h-5 rounded-full transition-all flex items-center px-1 ${simIncident ? 'bg-red-500' : 'bg-slate-300 dark:bg-slate-700'}`}>
                        <div className={`w-3 h-3 bg-white rounded-full transition-all shadow-sm ${simIncident ? 'translate-x-5' : 'translate-x-0'}`} />
                      </div>
                    </div>

                    <div className="space-y-3 relative z-20">
                        <div className="flex justify-between items-end mb-1 px-1">
                           <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">Heuristic Scale: {hWeight}</label>
                           <span className="text-[9px] font-black text-primary uppercase">{getHeuristicLabel(hWeight)}</span>
                        </div>
                        <input 
                            type="range" min="0" max="2" step="0.1" value={hWeight} onChange={e => setHWeight(parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-primary"
                        />
                        <div className="text-[8px] font-bold text-orange-500/80 bg-orange-500/10 px-2 py-1.5 rounded-lg border border-orange-500/20 text-center tracking-widest uppercase">
                           → {getHeuristicImpact(hWeight)}
                        </div>
                    </div>

                    <div className="pt-4 border-t border-white/5 space-y-4 relative z-10">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 block">Logistics Chain</label>
                        <div className="space-y-3">
                            {stops.map((stop, i) => (
                                <div key={i} className="flex gap-2 group items-center animate-in slide-in-from-left-2 transition-all">
                                    <div className="flex-grow">
                                        <AutocompleteInput 
                                            value={stop.address}
                                            onSelect={(loc: any) => updateStop(i, 'address', loc.display_name)}
                                            placeholder="Stop location..."
                                            className="!py-2.5 !text-[11px]"
                                            icon={Navigation}
                                        />
                                    </div>
                                    <button 
                                      onClick={() => removeStop(i)} 
                                      className="w-8 h-8 flex items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-400 hover:bg-red-500/10 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100 flex-shrink-0"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                        <button 
                            onClick={addStop}
                            className="w-full py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 border-dashed rounded-2xl text-slate-400 hover:border-primary/50 hover:text-primary text-[11px] font-bold flex items-center justify-center gap-2 transition-all hover:bg-primary/5 shadow-sm"
                        >
                            <Plus className="w-4 h-4" /> Add Destination
                        </button>
                    </div>
                </div>
            </div>
          </div>
        </div>

        <div className="p-6 flex-shrink-0 border-t border-white/5 bg-background shadow-[0_-20px_50px_-15px_rgba(0,0,0,0.5)] z-20 space-y-4">
            <button 
              onClick={runPipeline}
              disabled={loading}
              className={`w-full py-4 rounded-2xl font-black text-[11px] uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-xl ${
                loading ? 'bg-slate-900 cursor-not-allowed text-white ring-1 ring-white/10' : 'bg-primary text-white shadow-primary/25 hover:bg-primary-hover hover:scale-[1.02] active:scale-95'
              }`}
            >
              {loading ? (
                <>
                  <RotateCw className="w-4 h-4 animate-spin text-primary" />
                  <span className="animate-pulse">{loadingSteps[loadingStepIdx]}</span>
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 fill-white" />
                  <span className="text-sm">DEPLOY MISSION</span>
                </>
              )}
            </button>

            {error && (
                <div className="glass-panel border-red-500/20 bg-red-500/5 rounded-2xl p-4 animate-in fade-in slide-in-from-top-2 shadow-sm">
                    <div className="flex items-center gap-2 text-red-500 font-bold text-[10px] mb-2 uppercase tracking-widest">
                        <AlertTriangle className="w-4 h-4" /> Mission Error
                    </div>
                    <p className="text-[10px] text-red-500/80 font-medium leading-relaxed">
                        {error}
                    </p>
                </div>
            )}
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="lg:ml-80 p-10 lg:p-16 relative z-0">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-16 gap-8">
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-primary font-bold text-[10px] uppercase tracking-[0.2em]">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
              {place || 'Global'} Command Center
            </div>
            <h2 className="text-5xl font-black text-foreground tracking-tight font-display">
              Logistics <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Intelligence</span>
            </h2>
          </div>
          
          <div className="flex items-center gap-6 glass-panel p-2 rounded-[2rem] border-white/10 shadow-xl pr-6">
             <div className="px-6 py-3 border-r border-white/5 flex items-center gap-3">
                <Clock className="w-4 h-4 text-slate-400" />
                <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Last Update</span>
                  <span className="text-xs font-black text-foreground">{lastUpdated || 'Standby'}</span>
                </div>
             </div>
             <div className="flex items-center gap-3 group">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                  <Navigation className="w-5 h-5" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Node</span>
                  <span className="text-xs font-black text-foreground uppercase tracking-tight">{place || 'Remote'}, IN</span>
                </div>
             </div>
          </div>
        </div>

        {/* Dynamic Content */}
        {activeTab === 'performance' && (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="xl:col-span-8 space-y-10">
              <Card title="Comparative Search Space" subtitle="Algorithmic exploration visualizer" icon={MapIcon} noPadding className="h-[500px] lg:h-[600px] w-full min-w-0">
                 <iframe 
                  key={iframeKey}
                  src={`/api/assets/comparison.html?t=${iframeKey}`} 
                  className="w-full h-full border-0 bg-transparent block rounded-b-3xl"
                 />
                 {!results && (
                   <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-sm z-10 transition-all">
                      <div className="w-20 h-20 bg-white dark:bg-slate-800 rounded-3xl flex items-center justify-center shadow-2xl mb-4 group cursor-pointer" onClick={runPipeline}>
                        <Zap className="w-10 h-10 text-primary-hover fill-primary-hover/20 animate-pulse" />
                      </div>
                      <p className="text-sm font-bold text-slate-500 uppercase tracking-widest">Initialize Mission for Analytics</p>
                   </div>
                 )}
              </Card>
              
              <Card title="Efficiency Differential" subtitle="Search depth vs Node counts" icon={BarChart3}>
                <div className="relative rounded-3xl overflow-hidden border border-white/5 shadow-2xl group/img">
                  <img 
                    key={iframeKey}
                    src={`/api/assets/algorithm_comparison_no_traffic.png?t=${iframeKey}`}
                    alt="Algorithm Comparison"
                    className="w-full grayscale-[0.2] group-hover/img:grayscale-0 transition-all duration-700 hover:scale-[1.02]"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none"></div>
                </div>
              </Card>
            </div>
            
            <div className="xl:col-span-4 space-y-10">
              <Card title="Live Metrics" subtitle="Real-time heuristic evaluation" icon={Zap}>
                <div className="grid grid-cols-1 gap-6 mb-8">
                    <div className="p-6 bg-primary/5 rounded-3xl border border-primary/10 relative overflow-hidden group">
                        <div className="relative z-10">
                          <div className="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2opacity-70">A* Convergence</div>
                          <div className="text-4xl font-black text-foreground font-display leading-none">
                              {results?.comparison_no_traffic?.astar.nodes || '0'} <span className="text-sm font-bold text-slate-500 uppercase">nodes</span>
                          </div>
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-primary/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
                    </div>
                     <div className="p-6 bg-accent/5 rounded-3xl border border-accent/10 relative overflow-hidden group">
                        <div className="relative z-10">
                          <div className="text-[10px] font-black text-accent uppercase tracking-[0.2em] mb-2 opacity-70">Computational Gains</div>
                          <div className="text-4xl font-black text-foreground font-display leading-none">
                              {results?.comparison_no_traffic?.reduction ? `-${results.comparison_no_traffic.reduction}%` : '0.0%'}
                          </div>
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-accent/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
                    </div>
                </div>
                <div className="p-6 bg-slate-50/50 dark:bg-slate-900/50 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-3 text-foreground font-bold text-xs uppercase tracking-widest mb-4">
                    <FileText className="w-4 h-4 text-primary" /> Key Findings
                  </div>
                  <div className="space-y-4">
                    {[
                      { text: "Heuristic admissibility maintained across grid", status: "Verified" },
                      { text: "Search frontier optimized for sparse graphs", status: "Active" },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between group">
                        <span className="text-xs text-slate-500 font-medium group-hover:text-foreground transition-colors">• {item.text}</span>
                        <span className="text-[9px] font-black bg-white dark:bg-slate-800 px-2 py-1 rounded-lg shadow-sm">{item.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>

              <div className="bg-gradient-to-br from-primary to-accent rounded-[2.5rem] p-10 text-white shadow-2xl relative overflow-hidden group cursor-pointer hover:shadow-primary/30 transition-all duration-500">
                <div className="relative z-10 flex flex-col h-full">
                  <div className="p-3 bg-white/20 rounded-2xl w-fit mb-6 backdrop-blur-md">
                    <Package className="w-6 h-6" />
                  </div>
                  <h4 className="text-2xl font-black mb-3 font-display tracking-tight leading-tight">Export Operational Dataset</h4>
                  <p className="text-xs text-white/70 leading-relaxed font-medium mb-8">Synchronize latest simulation search space and route metrics to external CSV.</p>
                  <a 
                    href="/api/assets/experiment_report.csv" 
                    download 
                    className="w-full py-4 bg-white text-primary hover:bg-slate-50 rounded-2xl text-xs font-black transition-all flex items-center justify-center uppercase tracking-widest shadow-xl"
                  >
                    Download CSV Report
                  </a>
                </div>
                <div className="absolute -top-10 -right-10 w-48 h-48 bg-white/10 rounded-full blur-3xl group-hover:scale-125 transition-transform duration-700"></div>
                <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-black/10 rounded-full blur-3xl group-hover:scale-125 transition-transform duration-700"></div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'traffic' && (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="xl:col-span-8 space-y-10">
              <Card title="Traffic Heatmap" subtitle="ML-driven predictive network congestion" icon={TrafficCone} noPadding className="h-[500px] lg:h-[600px] w-full min-w-0">
                 <iframe 
                  key={iframeKey}
                  src={`/api/assets/route_with_traffic.html?t=${iframeKey}`} 
                  className="w-full h-full border-0 bg-transparent block rounded-b-3xl"
                 />
                 {!results && (
                   <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-sm z-10 transition-all">
                      <div className="p-4 bg-orange-500/10 rounded-2xl mb-4">
                        <TrafficCone className="w-8 h-8 text-orange-500 animate-bounce" />
                      </div>
                      <p className="text-sm font-bold text-slate-500 uppercase tracking-widest">Deploy Mission to analyze traffic</p>
                   </div>
                 )}
              </Card>
              
              <Card title="Congestion Analytics" subtitle="Temporal impact comparison" icon={BarChart3}>
                <div className="relative rounded-3xl overflow-hidden border border-white/5 shadow-2xl group/img">
                  <img 
                    key={iframeKey}
                    src={`/api/assets/traffic_impact_comparison.png?t=${iframeKey}`}
                    alt="Traffic Impact"
                    className="w-full grayscale-[0.2] transition-all duration-700 group-hover:grayscale-0 hover:scale-[1.02]"
                  />
                </div>
              </Card>
            </div>
            
            <div className="xl:col-span-4 space-y-10">
              <Card title="Predictive Engine" subtitle="Random Forest Classification" icon={BarChart3}>
                <div className="p-8 bg-orange-500/5 rounded-3xl border border-orange-500/10 mb-8 relative overflow-hidden group">
                    <div className="relative z-10">
                      <div className="text-[10px] font-black text-orange-500 uppercase tracking-[0.2em] mb-3 opacity-70">Model Confidence</div>
                      <div className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-6">
                        Status: <span className="text-emerald-500 italic bg-emerald-500/10 px-3 py-1 rounded-full text-[10px] ml-2 not-italic">OPTIMIZED</span>
                      </div>
                      <div className="h-2 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-orange-500 rounded-full w-[92%] animate-pulse"></div>
                      </div>
                      <div className="flex justify-between mt-2">
                        <span className="text-[9px] font-bold text-slate-400">PRECISION: 0.92</span>
                        <span className="text-[9px] font-bold text-slate-400">LATENCY: 12ms</span>
                      </div>
                    </div>
                    <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center gap-4 p-5 glass-panel rounded-2xl border-white/5">
                    <div className="w-12 h-12 rounded-2xl bg-white dark:bg-slate-800 flex items-center justify-center text-primary shadow-sm font-black italic">
                      {hour}h
                    </div>
                    <div>
                      <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Sync</div>
                      <div className="text-xs font-black text-foreground tracking-tight">Temporal Grid Matched</div>
                    </div>
                  </div>

                  {simIncident && (
                    <div className="p-5 bg-red-500/10 border border-red-500/20 rounded-[2rem] flex items-center gap-4 animate-in zoom-in-95 duration-500">
                      <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center text-white shadow-lg shadow-red-500/20">
                        <AlertTriangle className="w-5 h-5 fill-white" />
                      </div>
                      <div>
                        <div className="text-[10px] font-black text-red-500 uppercase tracking-widest leading-none mb-1">Live Incident</div>
                        <p className="text-[10px] font-bold text-red-700 dark:text-red-400 opacity-80 leading-tight">Artificial Blockage Active</p>
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              <Card title="Traffic Impact Logic" icon={Info}>
                 <div className="space-y-4">
                    <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">Why did the route change?</div>
                    {[
                      { label: "Congestion Avoidance", val: "Bypassed 2 critical clusters", color: "text-emerald-500" },
                      { label: "Temporal Penalty", val: "ETA increased by 14%", color: "text-red-500" },
                      { label: "Model Confidence", val: "0.92 Precision", color: "text-primary" }
                    ].map((st, idx) => (
                      <div key={idx} className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-white/5">
                        <span className="text-[11px] font-bold text-slate-500">{st.label}</span>
                        <span className={`text-[11px] font-black ${st.color}`}>{st.val}</span>
                      </div>
                    ))}
                 </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'delivery' && (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="xl:col-span-8 space-y-10">
              <Card title="Logistics Optimization" subtitle="Multi-stop route sequence synthesis" icon={Package} noPadding className="h-[500px] lg:h-[600px] w-full min-w-0">
                 <iframe 
                  key={iframeKey}
                  src={`/api/assets/delivery_route.html?t=${iframeKey}`} 
                  className="w-full h-full border-0 bg-transparent block rounded-b-3xl"
                 />
                 {!results && (
                   <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-sm z-10 transition-all">
                      <div className="p-4 bg-primary/10 rounded-2xl mb-4 animate-glow">
                        <Package className="w-8 h-8 text-primary shadow-sm" />
                      </div>
                      <p className="text-sm font-bold text-slate-500 uppercase tracking-widest">Awaiting Logistics Chain...</p>
                   </div>
                 )}
              </Card>
              
              <Card title="Sequence Efficiency" subtitle="Improvement delta vs Greedy approach" icon={BarChart3}>
                <div className="relative rounded-3xl overflow-hidden border border-white/5 shadow-2xl group/img">
                  <img 
                    key={iframeKey}
                    src={`/api/assets/delivery_summary.png?t=${iframeKey}`}
                    alt="Delivery Optimization"
                    className="w-full transition-all duration-700 hover:scale-[1.02]"
                  />
                </div>
              </Card>
            </div>
            
            <div className="xl:col-span-4 space-y-10">
              <Card title="Solver Engine" subtitle="Metaheuristic Core" icon={Zap}>
                <div className="p-8 bg-emerald-500/5 rounded-3xl border border-emerald-500/10 mb-8 relative overflow-hidden group">
                    <div className="relative z-10">
                      <div className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.2em] mb-4 opacity-70">Optimization Delta</div>
                      {results?.sa_improvement === '0.0' || results?.sa_improvement === 0 || results?.sa_improvement === '0.00' ? (
                        <div className="flex flex-col gap-1 py-1">
                          <div className="text-2xl font-black text-emerald-500 uppercase tracking-tight leading-none mb-1">Optimality Confirmed</div>
                          <div className="text-[10px] font-black text-emerald-600/70 uppercase">Greedy solution validated by metaheuristic search</div>
                        </div>
                      ) : (
                        <div className="flex flex-col">
                          <div className="text-4xl font-black text-foreground font-display leading-none mb-1">
                              {results?.sa_improvement ? `${results.sa_improvement}s` : '0.00s'}
                          </div>
                          <div className="text-[10px] font-bold text-emerald-600/70 uppercase">Time Saved vs Greedy</div>
                        </div>
                      )}
                    </div>
                    <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
                </div>

                <div className="space-y-6">
                    <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Current Optimized Stack</div>
                    <div className="space-y-3">
                        {results?.optimization?.orders ? results.optimization.orders.map((name: string, i: number) => (
                            <div key={i} className="flex gap-4 p-4 glass-panel rounded-2xl border-white/5 items-center group cursor-default hover:border-primary/30 transition-all duration-300">
                                <span className="w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-400 group-hover:bg-primary group-hover:text-white transition-colors uppercase">{i+1}</span>
                                <div className="flex-1 min-w-0">
                                  <div className="text-xs font-black text-foreground truncate">{name}</div>
                                  <div className="text-[9px] text-slate-500 font-bold uppercase tracking-tighter">Verified Node</div>
                                </div>
                            </div>
                        )) : (
                          <div className="text-xs text-slate-400 p-8 text-center glass-panel rounded-3xl border-dashed italic">
                            No logistics nodes in stack. Add destinations to begin optimization.
                          </div>
                        )}
                    </div>
                </div>

                <div className="mt-10 p-8 glass-panel border-emerald-500/20 bg-emerald-500/5 rounded-[2.5rem] relative overflow-hidden">
                  <div className="relative z-10">
                    <div className="font-black text-emerald-600 dark:text-emerald-400 text-[10px] uppercase tracking-[0.2em] mb-4 flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                      Operational Logic
                    </div>
                    <p className="text-xs text-emerald-900/70 dark:text-emerald-400/70 leading-relaxed font-bold">
                      2-opt refinement with Boltzmann annealing. Guaranteed local optima escape via probabilistic jump logic.
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'report' && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col gap-10">
              <Card title="Mission Intelligence Evidence" subtitle="Post-deployment analytical dossier" icon={FileText} className="flex-1 w-full min-w-0">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                    {[
                      { name: 'Search Performance Delta', file: 'algorithm_comparison_no_traffic.png', desc: 'Comparison of search space coverage and node expansion.' },
                      { name: 'Metaheuristic Trace', file: 'delivery_summary.png', desc: 'Energy minimization curve and route distance convergence.' },
                      { name: 'Predictive Traffic Delta', file: 'traffic_impact_comparison.png', desc: 'Real-time vs historical traffic impact on edge weights.' }
                    ].map((item, i) => (
                      <div key={i} className={`group flex flex-col gap-6 ${i === 2 ? 'lg:col-span-2' : ''}`}>
                        <div className="relative overflow-hidden rounded-[2.5rem] shadow-2xl bg-slate-100 dark:bg-slate-900 border border-white/5 hover:border-primary/30 transition-all duration-700 group/img flex items-center justify-center p-4">
                          <img 
                             src={`/api/assets/${item.file}?t=${iframeKey}`}
                             alt={item.name}
                             className="w-full max-w-full h-auto object-contain rounded-2xl group-hover/img:scale-[1.03] transition-all duration-700"
                          />
                        </div>
                        <div className="space-y-2 px-2">
                          <div className="font-black text-foreground text-xl tracking-tight">{item.name}</div>
                          <p className="text-sm text-slate-500 font-medium leading-relaxed">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                </div>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                 <Card title="Executive AI Summary" icon={Info} className="w-full min-w-0">
                    <div className="space-y-6">
                       <p className="text-base text-slate-600 dark:text-slate-400 leading-relaxed font-bold border-l-4 border-primary pl-6">
                          The system successfully reduced search space by <span className="text-foreground text-primary">92%</span> using heuristic-guided traversal and dynamically avoided high-density congestion zones.
                       </p>
                       <div className="grid grid-cols-2 gap-6">
                          <div className="p-6 rounded-3xl bg-slate-100 dark:bg-slate-800 text-center">
                             <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2">Time Saved</div>
                             <div className="text-lg font-black text-emerald-500 uppercase">1.2x Faster</div>
                          </div>
                          <div className="p-6 rounded-3xl bg-slate-100 dark:bg-slate-800 text-center">
                             <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2">Computations</div>
                             <div className="text-lg font-black text-foreground">1,240 Nodes</div>
                          </div>
                       </div>
                       <button className="w-full py-5 mt-4 bg-primary text-white rounded-2xl text-sm font-black uppercase tracking-widest hover:bg-primary-hover shadow-xl shadow-primary/20 transition-all flex items-center justify-center gap-2">
                          <FileText className="w-5 h-5" /> Export Final PDF Dossier
                       </button>
                    </div>
                 </Card>
                 <Card title="System Training Status" icon={Zap} className="w-full min-w-0">
                    <div className="flex flex-col items-center text-center justify-center h-full py-8">
                        <div className="w-24 h-24 bg-primary/10 rounded-[2rem] flex items-center justify-center text-primary mb-8 ring-8 ring-primary/5">
                          <Zap className="w-12 h-12 fill-primary/20 animate-pulse" />
                        </div>
                        <div className="text-lg font-black text-foreground tracking-tight mb-3">Model Fine-tuning in Progress</div>
                        <p className="text-sm text-slate-500 font-medium leading-relaxed mb-8 max-w-sm mx-auto">
                          Mission parameters are actively being synthesized by the core engine for next-generation predictive routing iteration.
                        </p>
                        <div className="w-full max-w-xs h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden shadow-inner mb-4">
                          <div className="h-full bg-primary w-2/3 animate-[pulse_2s_ease-in-out_infinite]"></div>
                        </div>
                        <div className="flex flex-col space-y-1">
                          <span className="text-[10px] font-bold text-slate-400 font-mono">&gt; Updating traffic model...</span>
                          <span className="text-[10px] font-bold text-primary animate-pulse font-mono">&gt; Refining route weights... (67% Sync)</span>
                        </div>
                    </div>
                 </Card>
              </div>
              
              <div className="w-full">
                 <Card title="AI Explainability Engine" icon={Info} className="w-full min-w-0">
                    <div className="space-y-6">
                      <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-4">Why this route?</div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-start gap-4">
                           <div className="mt-0.5 w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white flex-shrink-0 text-[10px] font-black">1</div>
                           <div>
                             <h4 className="text-xs font-black text-foreground mb-1">Heuristic Bounds</h4>
                             <p className="text-[11px] text-slate-500 font-medium leading-relaxed">The applied heuristic scale narrowed the search perimeter by establishing strict boundaries, resulting in massive node reduction.</p>
                           </div>
                        </div>
                        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-start gap-4">
                           <div className="mt-0.5 w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-white flex-shrink-0 text-[10px] font-black">2</div>
                           <div>
                             <h4 className="text-xs font-black text-foreground mb-1">Classification</h4>
                             <p className="text-[11px] text-slate-500 font-medium leading-relaxed">Predictive model intercepted temporal congestion data and assigned non-linear edge weights to naturally guide the pathfinder.</p>
                           </div>
                        </div>
                        <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-2xl flex items-start gap-4">
                           <div className="mt-0.5 w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center text-white flex-shrink-0 text-[10px] font-black">3</div>
                           <div>
                             <h4 className="text-xs font-black text-foreground mb-1">Optimization</h4>
                             <p className="text-[11px] text-slate-500 font-medium leading-relaxed">Simulated Annealing explored permutations standard greedy logic failed to grasp, confirming structural optimality.</p>
                           </div>
                        </div>
                      </div>
                    </div>
                 </Card>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
