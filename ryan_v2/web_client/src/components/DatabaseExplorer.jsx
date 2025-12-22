import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Database, MessageSquare, X, Plus, Filter, Loader2, Send, Check, ChevronDown, ArrowUpRight, Hash, Clock, Settings, RotateCw, Code, EyeOff, Download } from 'lucide-react';
import clsx from 'clsx';
import { marked } from 'marked';

const AVAILABLE_MODELS = [
    { name: "Claude 4.5 Sonnet", id: "anthropic:claude-sonnet-4-5-20250929" },
    { name: "Claude 4.5 Opus", id: "anthropic:claude-opus-4-5-20251101" },
    { name: "GPT-5.1", id: "openai:gpt-5.1" },
    { name: "o3-mini", id: "openai:o3-mini" },
    { name: "Gemini 1.5 Pro", id: "google:gemini-1.5-pro" },
];

// --- Sub-Components ---

function ResultsGrid({ results, onRowClick, selectedRowIndex }) {
    if (!results) return null;

    return (
        <div className="flex-1 overflow-auto bg-white relative">
            <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-[#fbf7e8] z-10 shadow-sm text-xs font-bold text-[#5a646a]">
                    <tr>
                        {results.columns.map(col => (
                            <th key={col} className="p-3 border-b border-[#e6dccb] whitespace-nowrap min-w-[100px] hover:bg-[#eaddcf]/30 transition-colors">
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-[#fbf7e8] text-xs font-mono text-[#394348]">
                    {results.rows.map((row, i) => (
                        <tr
                            key={i}
                            onClick={() => onRowClick(row, i)}
                            className={clsx(
                                "hover:bg-[#FFF8E7] transition-colors cursor-pointer border-l-4",
                                selectedRowIndex === i ? "bg-[#FFF8E7] border-l-[#9D7861]" : "border-l-transparent"
                            )}
                        >
                            {results.columns.map(col => (
                                <td key={col} className="p-2 border-r border-[#fbf7e8] whitespace-nowrap max-w-xs truncate px-3">
                                    {row[col] === null ? <span className="text-gray-300 italic">null</span> : String(row[col])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// --- Main Tab Content Component ---

function TabContent({
    type, // 'chat' or 'table'
    label,
    initialQuery,
    triggerExecute, // only relevant for 'chat' or initial load
    isActive,
    onRowSelect // NEW: Prop to notify parent
}) {
    // Shared State
    const [query, setQuery] = useState(initialQuery || "");
    const [results, setResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Chat Specific State
    const [naturalInput, setNaturalInput] = useState("");
    const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0]);
    const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Table Specific State
    const [selectedRowIndex, setSelectedRowIndex] = useState(null);
    const [selectedRowData, setSelectedRowData] = useState(null);
    const [filterText, setFilterText] = useState("");

    // Resizing Logic
    const [resultsHeight, setResultsHeight] = useState(400);
    const [isResizing, setIsResizing] = useState(false);
    const resultsRef = useRef(null);

    // Auto-execute effect
    useEffect(() => {
        if (triggerExecute > 0 && query && !results) {
            if (type === 'table') {
                // For tables, we might want to just run "SELECT * FROM tableName LIMIT 50" if query is table name
                // But parent likely passed full SQL: "SELECT * FROM ..."
                handleExecute(query);
            } else {
                handleExecute(query);
            }
        }
    }, [triggerExecute, query]);

    // Resizing Effect
    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isResizing) return;
            const newHeight = window.innerHeight - e.clientY;
            if (newHeight > 100 && newHeight < window.innerHeight * 0.8) {
                setResultsHeight(newHeight);
            }
        };
        const handleMouseUp = () => setIsResizing(false);
        if (isResizing) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);


    // Unified Chat History (User + AI Text)
    const [history, setHistory] = useState([]);

    // Footer state
    const [lastExecutionTime, setLastExecutionTime] = useState(null);
    const [lastQuery, setLastQuery] = useState("");

    const handleExecute = async (sqlToRun = query) => {
        if (!sqlToRun.trim()) return;

        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch("http://localhost:8000/api/sql/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sql: sqlToRun })
            });
            const data = await res.json();

            if (data.status === "error") {
                setError(data.error);
                setResults(null);
                // Add error to chat for visibility
                setHistory(prev => [...prev, {
                    role: 'assistant',
                    content: `❌ Query failed: ${data.error}`,
                    type: 'text'
                }]);
            } else {
                // Always show table results in grid
                setResults(data);
                setSelectedRowIndex(null);
                setSelectedRowData(null);

                // Add success message to chat
                const rowCount = data.rows ? data.rows.length : 0;
                setHistory(prev => [...prev, {
                    role: 'assistant',
                    content: `✅ Query executed successfully! Found ${rowCount} row${rowCount !== 1 ? 's' : ''}.`,
                    type: 'text'
                }]);

                // Update footer info
                setLastExecutionTime(new Date().toLocaleTimeString());
                setLastQuery(sqlToRun);
            }
        } catch (err) {
            const errorMsg = "Execution failed: " + err.message;
            setError(errorMsg);
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `❌ ${errorMsg}`,
                type: 'text'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateSQL = async () => {
        if (!naturalInput.trim()) return;

        // Add User Message to chat
        setHistory(prev => [...prev, { role: 'user', content: naturalInput, type: 'text' }]);
        const prompt = naturalInput;
        setNaturalInput(""); // Clear input

        setIsGenerating(true);
        setError(null);
        try {
            const res = await fetch("http://localhost:8000/api/sql/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: prompt,
                    model: selectedModel.id
                })
            });
            const data = await res.json();

            if (data.status === "error") {
                setError(data.error);
                // Add error message to chat
                setHistory(prev => [...prev, {
                    role: 'assistant',
                    content: `❌ Error generating SQL: ${data.error}`,
                    type: 'text'
                }]);
            } else {
                const generatedSQL = data.sql || "";

                // Add AI's SQL generation response to chat
                setHistory(prev => [...prev, {
                    role: 'assistant',
                    content: `I'll run this query:\n\`\`\`sql\n${generatedSQL}\n\`\`\``,
                    type: 'text'
                }]);

                // Auto-execute the generated SQL
                if (generatedSQL.trim()) {
                    await handleExecute(generatedSQL);
                }
            }
        } catch (err) {
            const errorMsg = "Failed to generate SQL: " + err.message;
            setError(errorMsg);
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `❌ ${errorMsg}`,
                type: 'text'
            }]);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleRowClick = (row, index) => {
        setSelectedRowIndex(index);
        setSelectedRowData(row);
        // Pass both row and label (which contains table name for table tabs)
        onRowSelect(row, label);
    };

    // Footer Action Handlers
    const handleClearResults = () => {
        setResults(null);
        setSelectedRowIndex(null);
        setSelectedRowData(null);
        setLastExecutionTime(null);
        setLastQuery("");
        setHistory(prev => [...prev, {
            role: 'assistant',
            content: 'Results cleared.',
            type: 'text'
        }]);
    };

    const handleRefreshQuery = async () => {
        if (lastQuery) {
            await handleExecute(lastQuery);
        }
    };

    const handleExportToExcel = async () => {
        if (!results || !results.rows || results.rows.length === 0) return;

        try {
            // Convert results to CSV format
            const headers = results.columns.join(',');
            const rows = results.rows.map(row =>
                results.columns.map(col => {
                    const val = row[col];
                    // Escape commas and quotes
                    if (val === null) return '';
                    const str = String(val);
                    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                        return `"${str.replace(/"/g, '""')}"`;
                    }
                    return str;
                }).join(',')
            ).join('\n');

            const csv = `${headers}\n${rows}`;

            // Create download link
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `query_results_${new Date().getTime()}.csv`;
            link.click();
            URL.revokeObjectURL(url);

            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `✅ Exported ${results.rows.length} rows to CSV.`,
                type: 'text'
            }]);
        } catch (err) {
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `❌ Export failed: ${err.message}`,
                type: 'text'
            }]);
        }
    };

    // Filter results based on filterText
    const filteredResults = useMemo(() => {
        if (!results || !filterText) return results;
        const lowerCaseFilter = filterText.toLowerCase();
        const filteredRows = results.rows.filter(row =>
            Object.values(row).some(value =>
                String(value).toLowerCase().includes(lowerCaseFilter)
            )
        );
        return { ...results, rows: filteredRows };
    }, [results, filterText]);

    if (!isActive) return <div className="hidden"></div>;

    // Split View Logic
    // If table view: Full height results (or loading)
    // If chat view: Top is History+Input, Bottom is Results (if present)

    return (
        <div className="flex-1 flex flex-col relative h-full">

            {/* 1. TABLE VIEW: Full Screen Grid */}
            {type === 'table' && (
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Filter Bar */}
                    <div className="h-10 bg-[#fbf7e8] border-b border-[#e6dccb] flex items-center px-4 gap-2 shrink-0">
                        <Filter size={14} className="text-[#9D7861]" />
                        <input
                            className="bg-transparent text-xs outline-none flex-1 placeholder-[#9D7861]/40 text-[#394348]"
                            placeholder="Filter results..."
                            value={filterText}
                            onChange={(e) => setFilterText(e.target.value)}
                        />
                    </div>

                    {results ? (
                        <div className="flex-1 flex flex-col h-full overflow-hidden">
                            <ResultsGrid
                                results={filteredResults}
                                onRowClick={handleRowClick}
                                selectedRowIndex={selectedRowIndex}
                            />
                            <div className="px-4 py-1.5 border-t border-[#e6dccb] bg-[#fbf7e8] text-[10px] text-[#9D7861] flex justify-between shrink-0">
                                <span>{results.total_rows} rows</span>
                                <span>{results.execution_time_ms}ms</span>
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-[#9D7861]/40 text-sm">
                            {isLoading ? <Loader2 className="animate-spin text-[#9D7861]" /> : "Loading table data..."}
                        </div>
                    )}
                </div>
            )}


            {/* 2. CHAT VIEW: Split Layout (History Top, Results Bottom) */}
            {type === 'chat' && (
                <div className="flex flex-col h-full overflow-hidden">

                    {/* Top: Chat History & Input (Takes all space initially, shares if results exist) */}
                    <div className="flex-1 flex flex-col min-h-0 relative">
                        {/* History Scroll Area */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {/* Empty State */}
                            {history.length === 0 && !results && (
                                <div className="text-center mt-20 animate-in fade-in zoom-in duration-700">
                                    <h1 className="font-display font-bold text-3xl text-[#394348] mb-2">AI Shell</h1>
                                    <p className="text-[#9D7861]/80 text-sm max-w-md mx-auto">
                                        Run SQL or ask questions about your data.
                                    </p>
                                </div>
                            )}

                            {history.map((msg, idx) => (
                                <div key={idx} className={clsx("flex w-full animate-in slide-in-from-bottom-2 fade-in duration-300", msg.role === 'user' ? "justify-end" : "justify-start")}>
                                    <div className={clsx(
                                        "max-w-[85%] rounded-lg px-5 py-3 text-sm leading-relaxed shadow-sm",
                                        msg.role === 'user'
                                            ? "bg-[#9D7861] text-white rounded-br-sm"
                                            : "bg-white text-[#394348] border border-[#e6dccb] rounded-bl-sm"
                                    )}>
                                        {msg.role === 'assistant' ? (
                                            <div
                                                className="markdown-content prose prose-sm max-w-none"
                                                dangerouslySetInnerHTML={{
                                                    __html: (() => {
                                                        try {
                                                            return marked.parse(msg.content || '');
                                                        } catch (e) {
                                                            console.error('Markdown parse error:', e);
                                                            return msg.content;
                                                        }
                                                    })()
                                                }}
                                            />
                                        ) : (
                                            <div className="whitespace-pre-wrap">{msg.content}</div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {/* Spacer for Input visibility */}
                            <div className="h-4" />
                        </div>

                        {/* Input Area (Pinned to Bottom of Top Section) */}
                        <div className="p-4 bg-[#fbf7e8] border-t border-[#e6dccb] shrink-0 z-10">
                            <div className="max-w-3xl mx-auto relative group">
                                <div className="bg-[#f0ece2] border border-[#d4c5b3] rounded-lg p-4 shadow-sm focus-within:shadow-md focus-within:border-[#9D7861] transition-all relative">
                                    <textarea
                                        value={naturalInput || query}
                                        onChange={(e) => {
                                            setNaturalInput(e.target.value);
                                            setQuery(e.target.value);
                                        }}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                const val = (naturalInput || query).trim().toUpperCase();
                                                if (val.startsWith('SELECT') || val.startsWith('WITH') || val.startsWith('PRAGMA')) {
                                                    handleExecute();
                                                } else {
                                                    handleGenerateSQL();
                                                }
                                            }
                                        }}
                                        placeholder="Type SQL or a question..."
                                        className="w-full bg-transparent border-none outline-none text-[#394348] text-sm font-medium placeholder-[#9D7861]/40 resize-none h-14 py-1"
                                    />
                                    {/* Footer Actions */}
                                    <div className="flex justify-between items-center mt-2">
                                        <div className="relative">
                                            <button onClick={() => setIsModelMenuOpen(!isModelMenuOpen)} className="flex items-center gap-1.5 px-3 py-1 bg-[#eaddcf]/50 hover:bg-[#eaddcf] rounded-full text-[11px] font-bold text-[#7d5b46] transition-colors">
                                                <span>{selectedModel.name.replace("Claude ", "").replace("GPT-", "")}</span>
                                                <ChevronDown size={12} className={clsx("transition-transform", isModelMenuOpen && "rotate-180")} />
                                            </button>
                                            {isModelMenuOpen && (
                                                <>
                                                    <div className="fixed inset-0 z-10" onClick={() => setIsModelMenuOpen(false)}></div>
                                                    <div className="absolute bottom-full left-0 mb-2 w-48 bg-white rounded-md shadow-xl border border-[#d4c5b3] py-1 z-20 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                                        {AVAILABLE_MODELS.map(model => (
                                                            <button key={model.id} onClick={() => { setSelectedModel(model); setIsModelMenuOpen(false); }} className="w-full text-left px-4 py-2 text-xs flex items-center justify-between hover:bg-[#fbf7e8] transition-colors">
                                                                <span className={clsx(selectedModel.id === model.id ? "text-[#9D7861] font-bold" : "text-[#5a646a]")}>{model.name}</span>
                                                                {selectedModel.id === model.id && <Check size={12} className="text-[#9D7861]" />}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                        <button onClick={() => (query.trim().toUpperCase().startsWith('SELECT') ? handleExecute() : handleGenerateSQL())} disabled={isLoading || isGenerating || (!naturalInput && !query)} className="p-2 bg-[#9D7861] text-white rounded-full hover:bg-[#7d5b46] disabled:opacity-50 transition-transform active:scale-95 shadow-md">
                                            {isLoading || isGenerating ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} className="ml-0.5" />}
                                        </button>
                                    </div>
                                </div>
                                {error && (
                                    <div className="mt-2 text-xs text-red-500 text-center">{error}</div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Bottom: Results Section (Conditional Split) */}
                    {results && (
                        <div className="h-[40%] min-h-[200px] border-t-2 border-[#d4c5b3]/50 flex flex-col bg-white shadow-[0_-4px_20px_-5px_rgba(0,0,0,0.1)] relative z-20 animate-in slide-in-from-bottom-10 duration-500">
                            {/* Results Header */}
                            <div className="h-8 bg-[#fbf7e8] border-b border-[#e6dccb] flex items-center justify-between px-4 shrink-0">
                                <span className="text-[10px] font-bold text-[#9D7861] uppercase tracking-wider flex items-center gap-2">
                                    <Database size={12} />
                                    Query Results
                                </span>
                                <div className="flex items-center gap-3 text-[10px] text-[#9D7861]/70">
                                    <span>{results.total_rows} rows</span>
                                    <span>{results.execution_time_ms}ms</span>
                                    <button onClick={() => setResults(null)} className="hover:text-[#9D7861] hover:bg-[#9D7861]/10 rounded p-0.5 transition-colors">
                                        <X size={12} />
                                    </button>
                                </div>
                            </div>

                            {/* Filter Bar */}
                            <div className="h-8 bg-white border-b border-[#fbf7e8] flex items-center px-4 gap-2 shrink-0">
                                <Filter size={12} className="text-[#9D7861]" />
                                <input
                                    className="bg-transparent text-xs outline-none flex-1 placeholder-[#9D7861]/40 text-[#394348]"
                                    placeholder="Filter results..."
                                    value={filterText}
                                    onChange={(e) => setFilterText(e.target.value)}
                                />
                            </div>

                            {/* The Grid */}
                            <div className="flex-1 overflow-hidden">
                                <ResultsGrid
                                    results={filteredResults}
                                    onRowClick={handleRowClick}
                                    selectedRowIndex={selectedRowIndex}
                                />
                            </div>
                        </div>
                    )}

                </div>
            )}
        </div>
    );
}


// --- Main DatabaseExplorer Component ---

export default function DatabaseExplorer({ initialQuery = "", triggerExecute = 0, openTableTab, onRowSelect }) {
    const [tabs, setTabs] = useState([
        { id: 'shell-1', type: 'chat', label: 'AI Shell #1', date: Date.now() }
    ]);
    const [activeTabId, setActiveTabId] = useState('shell-1');

    // Handle new tab requests from Sidebar
    useEffect(() => {
        if (openTableTab && openTableTab.tableName) {
            const table = openTableTab.tableName;
            // Check if tab exists
            const existingTab = tabs.find(t => t.type === 'table' && t.label === table);
            if (existingTab) {
                setActiveTabId(existingTab.id);
            } else {
                const newTab = {
                    id: `table - ${table} -${Date.now()} `,
                    type: 'table',
                    label: table,
                    initialQuery: `SELECT * FROM ${table} LIMIT 100`,
                    triggerExecute: Date.now(), // Force run
                    date: Date.now()
                };
                setTabs(prev => [...prev, newTab]);
                setActiveTabId(newTab.id);
            }
            // Signal consumption (optional if handled by parent reset, but good practice)
            if (openTableTab.reset) openTableTab.reset();
        }
    }, [openTableTab, tabs]);

    const closeTab = (e, id) => {
        e.stopPropagation();
        const newTabs = tabs.filter(t => t.id !== id);
        if (newTabs.length === 0) {
            // Ensure at least one shell
            const defaultTab = { id: 'shell-new', type: 'chat', label: 'AI Shell', date: Date.now() };
            setTabs([defaultTab]);
            setActiveTabId(defaultTab.id);
        } else {
            setTabs(newTabs);
            if (activeTabId === id) {
                setActiveTabId(newTabs[newTabs.length - 1].id);
            }
        }
    };

    const addTab = (type) => {
        const id = `${type} -${Date.now()} `;
        const newTab = {
            id,
            type,
            label: type === 'chat' ? 'New AI Chat' : 'New Table',
            date: Date.now()
        };
        setTabs([...tabs, newTab]);
        setActiveTabId(id);
    };

    return (
        <div className="flex flex-col h-full bg-[#fbf7e8] relative overflow-hidden">
            {/* Tab Bar */}
            <div className="h-10 bg-[#eaddcf]/30 border-b border-[#d4c5b3]/60 flex items-center px-4 gap-2 overflow-x-auto scrollbar-hide shrink-0">
                {tabs.map(tab => (
                    <div
                        key={tab.id}
                        onClick={() => setActiveTabId(tab.id)}
                        className={clsx(
                            "px-3 py-1.5 rounded-t-lg border-t border-x text-xs font-bold flex items-center gap-2 cursor-pointer transition-colors min-w-[120px] max-w-[200px] group select-none",
                            activeTabId === tab.id
                                ? "bg-[#fbf7e8] border-[#d4c5b3]/60 text-[#9D7861] translate-y-[1px]"
                                : "bg-transparent border-transparent text-[#9D7861]/60 hover:bg-[#fbf7e8]/50 hover:text-[#9D7861]"
                        )}
                    >
                        {tab.type === 'chat' ? <MessageSquare size={12} /> : <Database size={12} />}
                        <span className="truncate flex-1">{tab.label}</span>
                        <button onClick={(e) => closeTab(e, tab.id)} className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-[#9D7861]/10 rounded">
                            <X size={10} />
                        </button>
                    </div>
                ))}

                <button
                    onClick={() => addTab('chat')}
                    className="p-1 hover:bg-[#9D7861]/10 rounded text-[#9D7861]/60 hover:text-[#9D7861] transition-colors"
                    title="New Tab"
                >
                    <Plus size={16} />
                </button>
            </div>

            {/* Tab Content Area */}
            <div className="flex-1 relative overflow-hidden flex flex-col">
                {tabs.map(tab => (
                    <div
                        key={tab.id}
                        className={clsx("absolute inset-0 flex flex-col bg-[#fbf7e8]", activeTabId === tab.id ? "z-10" : "z-0 invisible")}
                    >
                        <TabContent
                            type={tab.type}
                            label={tab.label}
                            initialQuery={tab.initialQuery}
                            triggerExecute={tab.triggerExecute}
                            isActive={activeTabId === tab.id}
                            onRowSelect={onRowSelect}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
