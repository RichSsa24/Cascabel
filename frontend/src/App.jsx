import React, { useState, useEffect } from 'react';
import { Activity, Shield, Target, FileText, Database, ShieldAlert } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
  const [coverage, setCoverage] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [detections, setDetections] = useState([]);

  useEffect(() => {
    fetch('/api/coverage').then(res => res.json()).then(setCoverage).catch(console.error);
    fetch('/api/ledger').then(res => res.json()).then(setLedger).catch(console.error);
    fetch('/api/detections').then(res => res.json()).then(setDetections).catch(console.error);
  }, []);

  const coverageData = coverage ? Object.entries(coverage.tactics).map(([name, data]) => ({
    name: name.replace(' ', '\n'),
    covered: data.covered,
    pending: data.total - data.covered,
  })) : [];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <header className="mb-8 flex items-center gap-4 border-b border-slate-700 pb-4">
        <ShieldAlert className="w-10 h-10 text-emerald-400" />
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
            CASCABEL
          </h1>
          <p className="text-slate-400 text-sm">Purple-Team Emulation & Detection Synthesis</p>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex items-center gap-4 shadow-lg">
          <Target className="w-12 h-12 text-cyan-400" />
          <div>
            <p className="text-sm text-slate-400">Total Techniques</p>
            <p className="text-3xl font-bold">{coverage?.total_techniques || 0}</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex items-center gap-4 shadow-lg">
          <Shield className="w-12 h-12 text-emerald-400" />
          <div>
            <p className="text-sm text-slate-400">Covered & Proven</p>
            <p className="text-3xl font-bold">{coverage?.covered_techniques || 0}</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex items-center gap-4 shadow-lg">
          <FileText className="w-12 h-12 text-purple-400" />
          <div>
            <p className="text-sm text-slate-400">Synthesized Rules</p>
            <p className="text-3xl font-bold">{detections.length}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            ATT&CK Tactic Coverage Heatmap
          </h2>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={coverageData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                <XAxis dataKey="name" tick={{fill: '#94a3b8', fontSize: 12}} interval={0} angle={-45} textAnchor="end" />
                <YAxis tick={{fill: '#94a3b8'}} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Bar dataKey="covered" stackId="a" fill="#34d399" name="Covered" />
                <Bar dataKey="pending" stackId="a" fill="#334155" name="Pending" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col h-full">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Immutable Ledger Activity
          </h2>
          <div className="overflow-y-auto flex-1 h-80 pr-2 space-y-3">
            {ledger.map((entry, idx) => (
              <div key={idx} className="bg-slate-900 p-3 rounded border border-slate-700/50 flex flex-col gap-1">
                <div className="flex justify-between items-center">
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                    entry.action.includes('SUCCESS') ? 'bg-emerald-500/20 text-emerald-400' :
                    entry.action.includes('FAILED') || entry.action.includes('BLOCKED') ? 'bg-rose-500/20 text-rose-400' :
                    'bg-cyan-500/20 text-cyan-400'
                  }`}>
                    {entry.action}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="text-sm font-mono text-slate-300">
                  {entry.details?.technique && <span className="mr-3">Tactic: <span className="text-emerald-300">{entry.details.technique}</span></span>}
                  {entry.details?.target && <span>Target: <span className="text-cyan-300">{entry.details.target}</span></span>}
                </div>
              </div>
            ))}
            {ledger.length === 0 && <p className="text-slate-500 italic text-center py-10">No ledger entries yet.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
