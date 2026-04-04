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

const Card = ({ title, icon: Icon, children, className = "", noPadding = false }: any) => (
  <div className={`bg-white rounded-2xl shadow-xl border border-gray-100 transition-all duration-300 hover:shadow-2xl flex flex-col ${className}`}>
    <div className="bg-gradient-to-r from-blue-50 to-white px-6 py-4 flex items-center justify-between border-b border-gray-100 flex-shrink-0 rounded-t-2xl">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-600 rounded-lg text-white">
          <Icon className="w-5 h-5" />
        </div>
        <h3 className="font-bold text-gray-800 tracking-tight">{title}</h3>
      </div>
    </div>
    <div className={`flex-grow h-full ${noPadding ? "" : "p-6"}`}>
      {children}
    </div>
  </div>
);

const AutocompleteInput = ({ value, onChange, onSelect, placeholder, className = "" }: any) => {
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

  // Strategic Formatting: Venue vs context
  const formatLocation = (loc: any) => {
    const parts = loc.display_name.split(', ');
    const main = parts[0];
    const secondary = parts.slice(1, 4).join(', ');
    return { main, secondary };
  };

  return (
    <div className="relative w-full">
      <div className="relative group">
        <MapIcon className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
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
          className={`w-full pl-9 pr-8 py-2.5 bg-white border border-slate-200 rounded-xl text-[11px] font-bold focus:ring-4 focus:ring-blue-50 focus:border-blue-500 outline-none transition-all shadow-sm ${className}`}
        />
        {loading && (
          <div className="absolute right-3 top-2.5">
            <RotateCw className="w-3 h-3 text-blue-500 animate-spin" />
          </div>
        )}
      </div>

      {isOpen && suggestions.length > 0 && (
        <div className="absolute left-0 w-[320px] lg:w-[400px] mt-3 bg-white border border-slate-200 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.15)] z-[999] max-h-[450px] overflow-y-auto animate-in fade-in slide-in-from-top-2 ring-1 ring-slate-900/5 origin-top-left">
          <div className="p-3 border-b border-slate-50 bg-slate-50/50 sticky top-0 z-10 backdrop-blur-sm">
             <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">Location Intelligence</span>
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
                className="w-full text-left px-5 py-4 hover:bg-blue-50 transition-all border-l-4 border-l-transparent hover:border-l-blue-600 flex items-start gap-4 group"
              >
                <div className="mt-1 p-2 bg-slate-100 rounded-xl text-slate-400 group-hover:bg-blue-100 group-hover:text-blue-600 transition-colors flex-shrink-0">
                  <Navigation className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-black text-slate-800 leading-tight group-hover:text-blue-900 line-clamp-1">{main}</div>
                  <div className="text-[10px] font-bold text-slate-400 mt-1 line-clamp-2 leading-relaxed uppercase tracking-tighter">{secondary}</div>
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
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [iframeKey, setIframeKey] = useState(0);

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
    <div className="min-h-screen bg-[#F8FAFC] text-gray-900 font-sans selection:bg-blue-100">
      {/* ── Sidebar ── */}
      <aside className="fixed left-0 top-0 h-full w-80 bg-white border-r border-gray-200 z-50 p-6 hidden lg:block overflow-y-auto">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200">
            <Route className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tighter text-blue-900 leading-none">SmartRoute</h1>
            <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mt-1 block">AI Production Engine</span>
          </div>
        </div>

        <nav className="space-y-1 mb-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition-all duration-200 ${
                activeTab === tab.id 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' 
                  : 'text-gray-500 hover:bg-gray-50 hover:text-blue-600'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="text-sm">{tab.name}</span>
              {activeTab === tab.id && <ChevronRight className="ml-auto w-3 h-3 opacity-50" />}
            </button>
          ))}
        </nav>

        {/* Configuration Panel */}
        <div className="space-y-6">
            <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200">
                <div className="flex items-center gap-2 mb-4 text-slate-800 font-bold text-xs uppercase tracking-wider">
                    <Settings className="w-3 h-3" /> System Configuration
                </div>
                
                <div className="space-y-4">
                    <div>
                        <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">Simulation Environment</label>
                        <AutocompleteInput 
                            value={place} 
                            onSelect={(loc: any) => setPlace(loc.display_name)}
                            placeholder="Search City..."
                        />
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="text-[10px] font-bold text-slate-400 uppercase block">Time of Day: {hour}:00</label>
                        <Clock className="w-3 h-3 text-slate-300" />
                      </div>
                      <input 
                          type="range" min="0" max="23" step="1" value={hour} onChange={e => setHour(parseInt(e.target.value))}
                          className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                    </div>

                    <div className="flex items-center justify-between p-3 bg-white rounded-xl border border-slate-200">
                      <div>
                        <div className="text-[10px] font-bold text-slate-800 uppercase leading-none mb-1">Traffic Incident</div>
                        <div className="text-[9px] text-slate-400">Simulate random road block</div>
                      </div>
                      <button 
                        onClick={() => setSimIncident(!simIncident)}
                        className={`w-10 h-5 rounded-full transition-all flex items-center px-1 ${simIncident ? 'bg-red-500' : 'bg-slate-200'}`}
                      >
                        <div className={`w-3 h-3 bg-white rounded-full transition-all ${simIncident ? 'translate-x-5' : 'translate-x-0'}`} />
                      </button>
                    </div>

                    <div>
                        <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">AI Heuristic Scale: {hWeight}</label>
                        <input 
                            type="range" min="0" max="2" step="0.1" value={hWeight} onChange={e => setHWeight(parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                    </div>

                    <div className="pt-2 border-t border-slate-200">
                        <label className="text-[10px] font-bold text-slate-400 uppercase mb-2 block">Delivery Logistics</label>
                        <div className="space-y-3">
                            {stops.map((stop, i) => (
                                <div key={i} className="flex gap-2 group items-start">
                                    <div className="flex-grow">
                                        <AutocompleteInput 
                                            value={stop.address}
                                            onSelect={(loc: any) => updateStop(i, 'address', loc.display_name)}
                                            placeholder="Enter delivery stop..."
                                            className="!py-2.5 !text-[10px]"
                                        />
                                    </div>
                                    <button 
                                      onClick={() => removeStop(i)} 
                                      className="text-slate-300 hover:text-red-500 transition-colors pt-3 flex-shrink-0"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                        <button 
                            onClick={addStop}
                            className="w-full mt-3 py-2 border-2 border-dashed border-slate-200 rounded-lg text-slate-400 hover:border-blue-400 hover:text-blue-500 text-[10px] font-bold flex items-center justify-center gap-1 transition-all"
                        >
                            <Plus className="w-3 h-3" /> Add Destination
                        </button>
                    </div>
                </div>
            </div>

            <button 
              onClick={runPipeline}
              disabled={loading}
              className={`w-full py-4 rounded-xl font-black text-sm flex items-center justify-center gap-2 transition-all shadow-xl shadow-blue-100 ${
                loading ? 'bg-slate-700 cursor-not-allowed text-white' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
              }`}
            >
              {loading ? <RotateCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
              {loading ? 'CALCULATING ENGINE...' : 'DEPLOY MISSION'}
            </button>

            {error && (
                <div className="bg-red-50 border border-red-100 rounded-xl p-4 animate-in fade-in slide-in-from-top-2 shadow-sm">
                    <div className="flex items-center gap-2 text-red-600 font-bold text-xs mb-2 uppercase tracking-wide">
                        <AlertTriangle className="w-3.5 h-3.5" /> Intelligence Failure
                    </div>
                    <div className="max-h-60 overflow-y-auto">
                        <pre className="text-[10px] text-red-700 leading-tight font-mono whitespace-pre-wrap p-2 bg-white/50 rounded-lg border border-red-100/50">
                            {error}
                        </pre>
                    </div>
                </div>
            )}
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="lg:ml-80 p-8 lg:p-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <div className="flex items-center gap-2 text-blue-600 font-bold text-xs uppercase tracking-widest mb-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
              {place} Strategic Ops Console
            </div>
            <h2 className="text-4xl font-black text-slate-900 tracking-tight">
              Predictive Route <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Intelligence</span>
            </h2>
          </div>
          
          <div className="flex items-center gap-4 bg-white p-2 rounded-2xl border border-gray-100 shadow-sm">
             <div className="px-4 py-2 border-r border-gray-100 flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-xs font-bold text-gray-500 uppercase tracking-tighter">
                  System Sync: <span className="text-gray-900">{lastUpdated || 'Offline'}</span>
                </span>
             </div>
             <div className="px-4 py-2 flex items-center gap-2">
                <Navigation className="w-4 h-4 text-blue-500" />
                <span className="text-xs font-bold text-gray-900 uppercase tracking-tighter">{place}, IN</span>
             </div>
          </div>
        </div>

        {/* Dynamic Content */}
        {activeTab === 'performance' && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-2 space-y-8">
              <Card title="Comparative Search Space Analysis" icon={MapIcon} noPadding className="h-[75vh] min-h-[600px]">
                 <iframe 
                  key={iframeKey}
                  src={`/api/assets/comparison.html?t=${iframeKey}`} 
                  className="w-full h-full border-0 bg-slate-50 block"
                 />
              </Card>
              
              <Card title="Algorithmic Depth Report" icon={BarChart3}>
                <img 
                  key={iframeKey}
                  src={`/api/assets/algorithm_comparison_no_traffic.png?t=${iframeKey}`}
                  alt="Algorithm Comparison Chart"
                  className="w-full rounded-xl shadow-lg border border-slate-100"
                />
              </Card>
            </div>
            
            <div className="space-y-8">
              <Card title="Live Model Analytics" icon={BarChart3}>
                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="p-4 bg-blue-50 rounded-2xl">
                        <div className="text-[10px] font-bold text-blue-400 uppercase mb-1">Nodes (A*)</div>
                        <div className="text-2xl font-black text-blue-900 leading-none">
                            {results?.comparison_no_traffic?.astar.nodes || '---'}
                        </div>
                    </div>
                     <div className="p-4 bg-green-50 rounded-2xl">
                        <div className="text-[10px] font-bold text-green-400 uppercase mb-1">Search Saved</div>
                        <div className="text-2xl font-black text-green-900 leading-none">
                            {results?.comparison_no_traffic?.reduction ? `${results.comparison_no_traffic.reduction}%` : '---'}
                        </div>
                    </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center gap-2 text-slate-700 font-bold text-sm mb-2">
                    <FileText className="w-4 h-4" /> AI Lab Findings
                  </div>
                  <div className="text-xs text-slate-600 leading-relaxed font-medium space-y-2">
                    <p>• A* with Haversine distance remains consistent and admissible.</p>
                    <p>• Search space reduction represents significant computational energy savings.</p>
                  </div>
                </div>
              </Card>
              <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden group">
                <div className="relative z-10">
                  <h4 className="text-xl font-bold mb-2">Experimental Export</h4>
                  <p className="text-sm text-blue-100 opacity-80 leading-relaxed mb-4">Latest simulation metrics have been exported to CSV for research documentation.</p>
                  <a 
                    href="/api/assets/experiment_report.csv" 
                    download 
                    className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-xs font-bold transition-all backdrop-blur-md border border-white/10 flex items-center justify-center"
                  >
                    Download Results.csv
                  </a>
                </div>
                <div className="absolute -bottom-10 -right-10 w-44 h-44 bg-white/10 rounded-full blur-3xl group-hover:scale-125 transition-transform duration-700"></div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'traffic' && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-2 space-y-8">
              <Card title="Predictive Traffic Heatmap" icon={TrafficCone} noPadding className="h-[75vh] min-h-[600px]">
                 <iframe 
                  key={iframeKey}
                  src={`/api/assets/route_with_traffic.html?t=${iframeKey}`} 
                  className="w-full h-full border-0 bg-slate-50 block"
                 />
              </Card>
              
              <Card title="Traffic Impact Analytics" icon={BarChart3}>
                <img 
                  key={iframeKey}
                  src={`/api/assets/traffic_impact_comparison.png?t=${iframeKey}`}
                  alt="Traffic Impact Comparison Chart"
                  className="w-full rounded-xl shadow-lg border border-slate-100"
                />
              </Card>
            </div>
            
            <div className="space-y-8">
              <Card title="ML Predictive Insights" icon={BarChart3}>
                <div className="p-4 bg-orange-50 rounded-2xl mb-4 ring-1 ring-orange-100">
                    <div className="text-[10px] font-bold text-orange-400 uppercase mb-1">Random Forest Prediction</div>
                    <div className="text-xs font-bold text-orange-900 mt-2">
                        Status: <span className="text-emerald-600 italic">Pre-trained on Road Graphs</span>
                    </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                    <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-blue-600 shadow-sm">
                      {hour}h
                    </div>
                    <div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase">Target Hour</div>
                      <div className="text-xs font-bold text-slate-800 tracking-tight">Simulation Sync</div>
                    </div>
                  </div>
                  {simIncident && (
                    <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 animate-pulse">
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                      <div className="text-[10px] font-bold text-red-700 uppercase">Live Incident Simulation Enabled</div>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'delivery' && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-2 space-y-8">
              <Card title="Advanced Metaheuristic Logistics" icon={Package} noPadding className="h-[75vh] min-h-[600px]">
                 <iframe 
                  key={iframeKey}
                  src={`/api/assets/delivery_route.html?t=${iframeKey}`} 
                  className="w-full h-full border-0 bg-slate-50 block"
                 />
              </Card>
              
              <Card title="Route Optimization Analysis" icon={BarChart3}>
                <img 
                  key={iframeKey}
                  src={`/api/assets/delivery_summary.png?t=${iframeKey}`}
                  alt="Delivery Optimization Summary Chart"
                  className="w-full rounded-xl shadow-lg border border-slate-100"
                />
              </Card>
            </div>
            
            <div className="space-y-8">
              <Card title="Metaheuristic Summary" icon={BarChart3}>
                <div className="p-4 bg-emerald-50 rounded-2xl mb-4 ring-1 ring-emerald-100">
                    <div className="text-[10px] font-bold text-emerald-400 uppercase mb-1">SA Improvement vs Greedy</div>
                    <div className="text-2xl font-black text-emerald-900 leading-none">
                        {results?.sa_improvement ? `${results.sa_improvement}s` : '---'}
                    </div>
                </div>
                <div className="space-y-4">
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Optimized Sequence</div>
                    <div className="text-[11px] font-bold text-slate-700 mt-2 space-y-1">
                        {results?.optimization?.orders ? results.optimization.orders.map((name: string, i: number) => (
                            <div key={i} className="flex gap-2 p-2 bg-slate-50 rounded-lg">
                                <span className="opacity-40">{i+1}.</span> {name}
                            </div>
                        )) : <div className="text-xs opacity-50 italic">No sequence yet</div>}
                    </div>
                </div>
                <div className="mt-6 p-5 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100">
                  <div className="font-bold text-emerald-800 text-sm mb-1 flex items-center gap-2">
                    <Zap className="w-4 h-4" /> Solver Engine
                  </div>
                  <p className="text-[10px] text-emerald-900 leading-relaxed font-bold opacity-70">
                    Proprietary merge of 2-opt Refinement and Simulated Annealing with Boltzmann acceptance logic.
                  </p>
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'report' && (
          <Card title="Full Mission Evidence Folder" icon={FileText} className="h-[85vh] min-h-[750px]">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                {[
                  { name: 'Algorithmic Delta', file: 'algorithm_comparison_no_traffic.png' },
                  { name: 'Optimization Graph', file: 'delivery_summary.png' },
                  { name: 'Traffic Delta', file: 'traffic_impact_comparison.png' }
                ].map((item, i) => (
                  <div key={i} className="group flex flex-col gap-2">
                    <img 
                       src={`/api/assets/${item.file}?t=${iframeKey}`}
                       alt={item.name}
                       className="rounded-xl shadow-md border hover:scale-[1.02] cursor-zoom-in transition-transform"
                    />
                    <div className="text-center font-bold text-slate-700 text-xs">{item.name}</div>
                  </div>
                ))}
            </div>
            <div className="mt-12 p-8 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
               <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-white rounded-2xl shadow-sm">
                    <Package className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <div className="text-xl font-black text-slate-800 tracking-tight">Mission Manifest Data</div>
                    <div className="text-xs font-bold text-slate-400">RAW DATA JSON OUTPUT</div>
                  </div>
               </div>
               <pre className="bg-slate-900 text-teal-400 p-6 rounded-2xl text-[10px] font-mono overflow-x-auto shadow-inner">
                  {results ? JSON.stringify(results, null, 4) : '// Deployment pending...'}
               </pre>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
}
