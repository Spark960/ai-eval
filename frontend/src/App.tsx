import { useState, useEffect, useCallback } from 'react';
import ConfigPanel from './components/ConfigPanel';
import LogStream from './components/LogStream';
import Results from './components/Results';
import { startEvaluation, type EvalConfig, type EvalResults } from './lib/api';

function App() {
  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<EvalResults | null>(null);
  const [backendHealth, setBackendHealth] = useState<'checking' | 'ok' | 'error'>('checking');
  const [healthMessage, setHealthMessage] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        setBackendHealth(data.status);
        setHealthMessage(data.message);
      })
      .catch(() => {
        setBackendHealth('error');
        setHealthMessage('Backend server unreachable');
      });
  }, []);

  const handleRun = async (config: EvalConfig) => {
    setIsRunning(true);
    setLogs([]);
    setResults(null);
    try {
      const data = await startEvaluation(config);
      setRunId(data.run_id);
    } catch (error) {
      console.error("Failed to start:", error);
      setIsRunning(false);
    }
  };

  const handleEvalComplete = useCallback((finalResults: EvalResults) => {
    setResults(finalResults);
    setIsRunning(false);
  }, []);
  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {backendHealth === 'error' && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md shadow-sm">
            <div className="flex items-center">
              <svg className="w-6 h-6 text-red-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              <div>
                <h3 className="text-red-800 font-bold">Health Check Failed</h3>
                <p className="text-red-700 text-sm mt-1">{healthMessage}. Ensure backend and Ollama are running.</p>
              </div>
            </div>
          </div>
        )}

        <header>
          <h1 className="text-3xl font-bold">Multimodal API Eval Framework</h1>
          <p className="text-gray-500">PoC v3.0 // Capability-Aware Router</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="col-span-1">
            <ConfigPanel onRun={handleRun} isRunning={isRunning} />
          </div>
          
          <div className="col-span-1 md:col-span-2 space-y-6">
            <LogStream 
              runId={runId} 
              logs={logs} 
              setLogs={setLogs} 
              onComplete={handleEvalComplete} 
            />
            
            {results && <Results data={results} />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;