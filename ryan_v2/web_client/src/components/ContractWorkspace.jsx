
import React, { useState, useEffect, useRef } from 'react';
import { FileText, ChevronRight, Download, Printer, Save, RefreshCw, Layers, Layout, Calendar, Clock, Euro, User, Building, Trash2, CheckCircle, AlertCircle, Info } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ContractWorkspace() {
    const [clients, setClients] = useState([]);
    const [houses, setHouses] = useState([]);
    const [history, setHistory] = useState([]);
    const [selectedClient, setSelectedClient] = useState('');
    const [selectedHouse, setSelectedHouse] = useState('');
    const [contractMd, setContractMd] = useState('');
    const [loading, setLoading] = useState(false);
    const [overrides, setOverrides] = useState({
        checkin_datum: '',
        checkout_datum: '',
        totale_huur_factuur: '',
        voorschot_gwe: '',
        betaalde_borg: '',
        eindschoonmaak: ''
    });
    const [status, setStatus] = useState('idle'); // idle, loading, success, error
    const previewRef = useRef(null);

    // Fetch initial dropdown data and history
    useEffect(() => {
        fetch('http://localhost:8000/api/contracts/data')
            .then(res => res.json())
            .then(data => {
                setClients(data.clients);
                setHouses(data.houses);
            })
            .catch(err => setStatus('error'));

        fetchHistory();
    }, []);

    const fetchHistory = () => {
        fetch('http://localhost:8000/api/contracts/list')
            .then(res => res.json())
            .then(data => setHistory(data.contracts))
            .catch(err => console.error("Failed to fetch history:", err));
    };

    // Fetch defaults when selection changes
    useEffect(() => {
        if (selectedClient && selectedHouse) {
            handlePrefill(true);
        }
    }, [selectedClient, selectedHouse]);

    const handlePrefill = (onlyData = false) => {
        if (!selectedClient || !selectedHouse) return;
        setLoading(true);
        setStatus('loading');

        fetch('http://localhost:8000/api/contracts/prefill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                klant_id: parseInt(selectedClient),
                object_id: selectedHouse,
                overrides: Object.fromEntries(Object.entries(overrides).filter(([_, v]) => v !== ''))
            })
        })
            .then(res => res.json())
            .then(data => {
                if (!onlyData) {
                    setContractMd(data.markdown);
                    setStatus('success');
                } else {
                    setOverrides(prev => ({
                        ...prev,
                        totale_huur_factuur: data.data.totale_huur_factuur || prev.totale_huur_factuur,
                        voorschot_gwe: data.data.voorschot_gwe || prev.voorschot_gwe,
                        betaalde_borg: data.data.betaalde_borg || prev.betaalde_borg,
                        eindschoonmaak: data.data.eindschoonmaak || prev.eindschoonmaak,
                    }));
                    setStatus('idle');
                }
                setLoading(false);
            })
            .catch(() => {
                setLoading(false);
                setStatus('error');
            });
    };

    const handleSaveToServer = () => {
        if (!contractMd) return;

        // Extract client and house name for filename
        const clientName = clients.find(c => String(c.id) === String(selectedClient))?.naam || "UnknownClient";
        const date = new Date().toISOString().split('T')[0];
        const filename = `${clientName}_${selectedHouse}_${date}.md`;

        fetch('http://localhost:8000/api/contracts/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, markdown: contractMd })
        })
            .then(res => res.json())
            .then(() => {
                fetchHistory();
                alert("Contract saved to server successfully!");
            })
            .catch(err => alert("Failed to save contract"));
    };

    const handleDownload = (filename) => {
        window.open(`http://localhost:8000/api/contracts/download/${filename}`, '_blank');
    };

    const handleReset = () => {
        setSelectedClient('');
        setSelectedHouse('');
        setContractMd('');
        setOverrides({
            checkin_datum: '',
            checkout_datum: '',
            totale_huur_factuur: '',
            voorschot_gwe: '',
            betaalde_borg: '',
            eindschoonmaak: ''
        });
        setStatus('idle');
    };

    return (
        <div className="h-full flex gap-6 p-8 bg-[#fbf7e8] font-worksans overflow-hidden">
            {/* Left Panel: Bento Controls */}
            <div className="w-[380px] shrink-0 flex flex-col gap-5 overflow-y-auto pr-2 scrollbar-thin">
                <header className="mb-1">
                    <span className="text-[10px] font-bold text-[#9D7861] uppercase tracking-[0.3em] mb-1 block">Contracting Engine</span>
                    <h1 className="font-barlow font-bold text-3xl text-[#394348] tracking-tight">RyanRent Contracts</h1>
                    <div className="h-1 w-10 bg-[#9D7861] mt-2 rounded-full"></div>
                </header>

                <div className="flex flex-col gap-5">
                    {/* Step 1: Selection */}
                    <div className="bg-white border border-[#e6dccb] p-6 rounded-[2rem] shadow-sm relative overflow-hidden group">
                        <div className="flex items-center gap-2 text-[#9D7861] mb-5 font-barlow font-bold uppercase tracking-widest text-[10px]">
                            <div className="w-5 h-5 rounded-full bg-[#9D7861] text-white flex items-center justify-center text-[9px] shadow-sm">1</div>
                            Entity Configuration
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-1">
                                <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1">Klant / Leverancier</label>
                                <select
                                    value={selectedClient}
                                    onChange={(e) => setSelectedClient(e.target.value)}
                                    className="w-full p-3 bg-[#fbf7e8]/40 border border-[#d4c5b3] rounded-xl text-xs outline-none focus:border-[#9D7861] transition-all appearance-none cursor-pointer"
                                >
                                    <option value="">Select client...</option>
                                    {clients.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
                                </select>
                            </div>

                            <div className="space-y-1">
                                <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1">Object ID</label>
                                <select
                                    value={selectedHouse}
                                    onChange={(e) => setSelectedHouse(e.target.value)}
                                    className="w-full p-3 bg-[#fbf7e8]/40 border border-[#d4c5b3] rounded-xl text-xs outline-none focus:border-[#9D7861] transition-all appearance-none cursor-pointer"
                                >
                                    <option value="">Select house...</option>
                                    {houses.map(h => <option key={h.object_id} value={h.object_id}>{h.object_id} — {h.adres}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Step 2: Terms & Financials */}
                    <div className="bg-white border border-[#e6dccb] p-6 rounded-[2rem] shadow-sm relative overflow-hidden">
                        <div className="flex items-center justify-between mb-5">
                            <div className="flex items-center gap-2 text-[#9D7861] font-barlow font-bold uppercase tracking-widest text-[10px]">
                                <div className="w-5 h-5 rounded-full bg-[#9D7861] text-white flex items-center justify-center text-[9px] shadow-sm">2</div>
                                Terms & Financials
                            </div>
                            {selectedHouse && (
                                <div className="flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full text-[9px] font-bold border border-emerald-100">
                                    <CheckCircle size={8} /> Linked
                                </div>
                            )}
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1">Start</label>
                                    <input
                                        type="date"
                                        value={overrides.checkin_datum}
                                        onChange={(e) => setOverrides({ ...overrides, checkin_datum: e.target.value })}
                                        className="w-full p-3 bg-[#f9f5eb] border border-[#d4c5b3] rounded-xl text-[10px] outline-none focus:border-[#9D7861]"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1">End</label>
                                    <input
                                        type="date"
                                        value={overrides.checkout_datum}
                                        onChange={(e) => setOverrides({ ...overrides, checkout_datum: e.target.value })}
                                        className="w-full p-3 bg-[#f9f5eb] border border-[#d4c5b3] rounded-xl text-[10px] outline-none focus:border-[#9D7861]"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1 flex items-center gap-1">Huur</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9D7861] font-bold text-[10px]">€</span>
                                        <input
                                            type="text"
                                            value={overrides.totale_huur_factuur}
                                            onChange={(e) => setOverrides({ ...overrides, totale_huur_factuur: e.target.value })}
                                            className="w-full pl-6 pr-3 py-3 bg-white border border-[#d4c5b3] rounded-xl text-[10px] font-bold outline-none focus:border-[#9D7861]"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1 flex items-center gap-1">GWE</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9D7861] font-bold text-[10px]">€</span>
                                        <input
                                            type="text"
                                            value={overrides.voorschot_gwe}
                                            onChange={(e) => setOverrides({ ...overrides, voorschot_gwe: e.target.value })}
                                            className="w-full pl-6 pr-3 py-3 bg-white border border-[#d4c5b3] rounded-xl text-[10px] font-bold outline-none focus:border-[#9D7861]"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1 flex items-center gap-1">Borg</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-600 font-bold text-[10px]">€</span>
                                        <input
                                            type="text"
                                            value={overrides.betaalde_borg}
                                            onChange={(e) => setOverrides({ ...overrides, betaalde_borg: e.target.value })}
                                            className="w-full pl-6 pr-3 py-3 bg-emerald-50/20 border border-emerald-100 rounded-xl text-[10px] font-bold text-emerald-900 outline-none"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1 flex items-center gap-1">Clean</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-600 font-bold text-[10px]">€</span>
                                        <input
                                            type="text"
                                            value={overrides.eindschoonmaak}
                                            onChange={(e) => setOverrides({ ...overrides, eindschoonmaak: e.target.value })}
                                            className="w-full pl-6 pr-3 py-3 bg-blue-50/20 border border-blue-100 rounded-xl text-[10px] font-bold text-blue-900 outline-none"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-3">
                    <button
                        onClick={() => handlePrefill()}
                        disabled={loading || !selectedClient || !selectedHouse}
                        className={clsx(
                            "w-full py-4 rounded-[1.5rem] font-barlow font-bold text-sm shadow-lg transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50",
                            status === 'success' ? "bg-emerald-600 text-white" : "bg-[#9D7861] text-white hover:bg-[#83624d]"
                        )}
                    >
                        {loading ? <RefreshCw className="animate-spin" size={18} /> : status === 'success' ? <CheckCircle size={18} /> : <RefreshCw size={18} />}
                        {status === 'success' ? 'Contract Formulated!' : 'Apply Pre-fill & Preview'}
                    </button>

                    <div className="flex gap-2">
                        <button
                            onClick={() => window.print()}
                            className="flex-1 py-3 bg-white border border-[#e6dccb] text-[#394348] rounded-[1.2rem] font-barlow font-bold text-[11px] flex items-center justify-center gap-2 hover:bg-[#fbf7e8] transition-colors shadow-sm"
                        >
                            <Printer size={14} className="text-[#9D7861]" /> Print PDF
                        </button>
                        <button
                            onClick={handleSaveToServer}
                            className="flex-1 py-3 bg-white border border-[#e6dccb] text-[#394348] rounded-[1.2rem] font-barlow font-bold text-[11px] flex items-center justify-center gap-2 hover:bg-[#fbf7e8] transition-colors shadow-sm"
                        >
                            <Save size={14} className="text-[#9D7861]" /> Save Server
                        </button>
                        <button
                            onClick={handleReset}
                            className="px-4 py-3 bg-white border border-[#e6dccb] text-red-500 rounded-[1.2rem] flex items-center justify-center hover:bg-red-50 transition-colors shadow-sm"
                        >
                            <Trash2 size={16} />
                        </button>
                    </div>
                </div>

                {/* History Panel - NEW */}
                <div className="flex-1 flex flex-col bg-white border border-[#e6dccb] rounded-[2rem] shadow-sm overflow-hidden min-h-[200px]">
                    <div className="px-5 py-4 border-b border-[#fbf7e8] flex items-center justify-between">
                        <div className="flex items-center gap-2 text-[#9D7861] font-barlow font-bold uppercase tracking-widest text-[9px]">
                            <Clock size={12} /> Recent Contracts
                        </div>
                        <button onClick={fetchHistory} className="text-gray-400 hover:text-[#9D7861] transition-colors">
                            <RefreshCw size={10} />
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
                        {history.length > 0 ? history.map((file, idx) => (
                            <div key={idx} className="group flex items-center justify-between p-3 rounded-xl hover:bg-[#fbf7e8] transition-all cursor-default">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                                        <FileText size={16} />
                                    </div>
                                    <div className="overflow-hidden">
                                        <p className="text-[11px] font-bold text-gray-700 truncate">{file.name}</p>
                                        <p className="text-[9px] text-gray-400">{new Date(file.created * 1000).toLocaleDateString()}</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDownload(file.name)}
                                    className="p-2 opacity-0 group-hover:opacity-100 text-[#9D7861] hover:bg-white rounded-lg transition-all"
                                    title="Download"
                                >
                                    <Download size={14} />
                                </button>
                            </div>
                        )) : (
                            <div className="h-full flex flex-col items-center justify-center text-gray-300 py-10">
                                <FileText size={32} opacity={0.3} />
                                <p className="text-[10px] mt-2">No history found</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Right Panel: GFM Grounded Preview */}
            <div className="flex-1 flex flex-col bg-white border border-[#e6dccb] rounded-[2.5rem] shadow-xl overflow-hidden print:m-0 print:border-none print:shadow-none relative">
                <div className="h-16 border-b border-[#fbf7e8] flex items-center justify-between px-8 bg-gray-50/50 print:hidden relative z-20">
                    <div className="flex items-center gap-3">
                        <div className={clsx(
                            "w-2 h-2 rounded-full transition-all duration-1000",
                            status === 'success' ? "bg-emerald-500 animate-pulse" : "bg-gray-300"
                        )} />
                        <div>
                            <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest block leading-none mb-1">Live Document Preview</span>
                            <span className="text-xs font-bold text-[#394348] font-barlow">{contractMd ? "Editing Mode Active" : "Waiting for Configuration..."}</span>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#e6dccb] rounded-full text-[9px] font-bold text-gray-600">
                            <Layout size={10} className="text-[#9D7861]" /> Barlow+WorkSans
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-12 bg-[#f4f1ea]/30 print:p-0 print:bg-white flex justify-center scrollbar-thin relative z-10">
                    <div
                        contentEditable={!!contractMd}
                        suppressContentEditableWarning
                        onInput={(e) => setContractMd(e.currentTarget.innerText)}
                        className={clsx(
                            "bg-white p-[2.5cm] min-h-[29.7cm] w-[21cm] shadow-xl outline-none print:shadow-none print:p-0 font-worksans text-[13px] leading-[1.6] text-gray-800 transition-all duration-500 relative",
                            contractMd ? "translate-y-0 opacity-100" : "translate-y-4 opacity-30 grayscale blur-[1px]"
                        )}
                        style={{ borderTop: '6px solid #9D7861' }}
                    >
                        {contractMd ? (
                            <div className="prose prose-sm max-w-none">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{contractMd}</ReactMarkdown>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-gray-300 gap-4 py-32">
                                <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
                                    <FileText size={32} strokeWidth={1} />
                                </div>
                                <div className="text-center">
                                    <p className="font-barlow font-bold text-xl text-gray-400 mb-1">No Draft Active</p>
                                    <p className="text-[10px] max-w-[200px] text-gray-400">Configure client and house on the left to start drafting. Your live changes here can be saved to the server.</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Shadow Grounding Elements */}
                    {!contractMd && (
                        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                            <div className="w-[19cm] h-[25cm] border-2 border-dashed border-[#e6dccb] rounded-[1.5cm]" />
                        </div>
                    )}
                </div>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                @media print {
                    @page { margin: 1.5cm; size: A4; }
                    body { background: white !important; }
                    .h-full { display: block !important; overflow: visible !important; height: auto !important; }
                    div[contenteditable] {
                        border: none !important;
                        box-shadow: none !important;
                        padding: 0 !important;
                    }
                }
                @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Work+Sans:wght@400;500;600;700&display=swap');
                
                .font-barlow { font-family: 'Barlow', sans-serif; }
                .font-worksans { font-family: 'Work Sans', sans-serif; }
                
                .scrollbar-thin::-webkit-scrollbar { width: 4px; }
                .scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
                .scrollbar-thin::-webkit-scrollbar-thumb { background: #e6dccb; border-radius: 10px; }
                
                input[type="date"]::-webkit-calendar-picker-indicator {
                    filter: invert(47%) sepia(21%) saturate(579%) hue-rotate(338deg) brightness(96%) contrast(85%);
                    cursor: pointer;
                }

                .prose { color: #1a1a1a; }
                .prose p { text-align: justify; line-height: 1.6; margin-bottom: 1.25rem; }
                .prose h1, .prose h2, .prose h3 { margin-top: 2rem; margin-bottom: 1rem; font-family: 'Barlow', sans-serif; font-weight: 700; color: #394348; }
                .prose h1 { font-size: 24px; border-bottom: 2px solid #fbf7e8; padding-bottom: 0.5rem; }
                .prose h2 { font-size: 18px; }
                .prose h3 { font-size: 15px; }
                .prose table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 12px; }
                .prose th { background-color: #f8f9fa; border: 1px solid #e2e8f0; padding: 10px; text-align: left; font-weight: 700; color: #4a5568; }
                .prose td { border: 1px solid #e2e8f0; padding: 10px; vertical-align: top; }
                .prose tr:nth-child(even) { background-color: #fcfcfc; }
                .prose hr { border: 0; border-top: 1px solid #edf2f7; margin: 2rem 0; }
                .prose img { margin-bottom: 2rem; max-width: 180px; }
                .prose ul, .prose ol { padding-left: 1.5rem; margin-bottom: 1rem; }
                .prose li { margin-bottom: 0.4rem; }
            `}} />
        </div>
    );
}

