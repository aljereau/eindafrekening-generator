import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Sparkles, Loader2, ChevronDown, ChevronRight, Terminal, Menu, Settings, Bell, Paperclip, FileText, FileIcon, Download, Hash, MessageSquare, Plus, Database, X, RotateCw, Braces } from 'lucide-react';
import clsx from 'clsx';
import DatabaseExplorer from './components/DatabaseExplorer';
import ContractWorkspace from './components/ContractWorkspace';

// --- Components ---

function Avatar({ name, initials, active, color }) {
  return (
    <div className="relative">
      <div className={clsx("w-10 h-10 rounded-full flex items-center justify-center text-white font-medium text-sm", color || "bg-emerald-600")}>
        {initials || name.slice(0, 2).toUpperCase()}
      </div>
      {active && <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-white rounded-full ring-1 ring-emerald-500/20"></div>}
    </div>
  );
}

// --- Global Components ---

function GlobalRail({ activeView, onSelectView, notifications = [] }) {
  const NavItem = ({ viewId, icon, label, hasNotification }) => (
    <button
      onClick={() => onSelectView(viewId)}
      className={clsx(
        "relative p-3 rounded-md transition-all duration-300 group",
        activeView === viewId
          ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/20 scale-105"
          : "text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 hover:scale-105"
      )}
      title={label}
    >
      {icon}
      {hasNotification && (
        <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full ring-2 ring-[#fbf7e8] animate-pulse" />
      )}
    </button>
  );
  return (
    <div className="w-20 py-8 flex flex-col items-center justify-between h-full bg-white border-r border-gray-100">
      {/* Top: Logo & Main Nav */}
      <div className="flex flex-col items-center gap-8 w-full">
        {/* Logo */}
        {/* Logo */}
        <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white font-display font-bold text-2xl cursor-default">
          <span className="mt-0.5">R</span>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-4 w-full px-4">
          <NavItem
            viewId="chat"
            icon={<MessageSquare size={22} />}
            label="Chat"
          />
          <NavItem
            viewId="database"
            icon={<Database size={22} />}
            label="Database"
          />
          <NavItem
            viewId="contracts"
            icon={<FileText size={22} />}
            label="Contracts"
          />
        </nav>
      </div>

      {/* Bottom: Settings & Profile */}
      <div className="flex flex-col items-center gap-6 w-full px-4 mb-4">
        <NavItem
          viewId="settings"
          icon={<Settings size={22} />}
          label="Settings"
        />
        <div className="h-px w-8 bg-gray-200 my-2"></div>
        {/* ... User Avatar ... */}
        <div className="relative group cursor-pointer">
          <Avatar name="Aljereau" initials="AM" color="bg-gray-800" />
          <div className="absolute left-full ml-4 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl">
            Aljereau Marten
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingsWorkspace({ activeModel, onModelChange, availableModels }) {
  const [activeTab, setActiveTab] = useState('general');

  return (
    <div className="h-full flex flex-col bg-[#fbf7e8] animate-in fade-in duration-300">
      {/* Header */}
      <div className="h-20 border-b border-[#e6dccb] flex items-center justify-between px-8 bg-[#fbf7e8]/50 backdrop-blur-md sticky top-0 z-10 w-full">
        <div className="flex items-center gap-4">
          <div className="p-2.5 bg-[#9D7861]/10 rounded-md text-[#9D7861]">
            <Settings size={24} />
          </div>
          <div>
            <h2 className="font-display font-bold text-xl text-[#394348]">Settings</h2>
            <p className="text-xs text-[#9D7861]">Configure your RyanRent experience</p>
          </div>
        </div>
      </div>

      {/* Tabs & Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Sidebar Tabs */}
        <div className="w-64 border-r border-[#e6dccb] p-6 space-y-2 bg-[#fbf7e8]/50">
          <button
            onClick={() => setActiveTab('general')}
            className={clsx(
              "w-full text-left px-4 py-3 rounded-md font-medium text-sm transition-all flex items-center gap-3",
              activeTab === 'general' ? "bg-[#9D7861] text-white shadow-md shadow-[#9D7861]/20" : "text-[#394348] hover:bg-[#9D7861]/10"
            )}
          >
            <Terminal size={18} />
            General
          </button>
          <button
            onClick={() => setActiveTab('appearance')}
            className={clsx(
              "w-full text-left px-4 py-3 rounded-md font-medium text-sm transition-all flex items-center gap-3",
              activeTab === 'appearance' ? "bg-[#9D7861] text-white shadow-md shadow-[#9D7861]/20" : "text-[#394348] hover:bg-[#9D7861]/10"
            )}
          >
            <Sparkles size={18} />
            Appearance
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'general' && (
            <div className="max-w-2xl space-y-8 animate-in slide-in-from-right-4 duration-500">
              <section>
                <h3 className="text-lg font-bold text-[#394348] mb-4 flex items-center gap-2">
                  <Bot size={20} className="text-[#9D7861]" />
                  AI Model Configuration
                </h3>
                <div className="bg-white border border-[#e6dccb] rounded-lg p-6 shadow-sm">
                  <label className="block text-xs font-bold text-[#9D7861] uppercase tracking-wider mb-3">Active Model Provider</label>
                  <div className="relative">
                    <select
                      value={activeModel}
                      onChange={(e) => onModelChange(e.target.value)}
                      className="w-full p-4 rounded-md bg-[#fbf7e8] border border-[#d4c5b3] text-sm text-[#394348] focus:outline-none focus:ring-2 focus:ring-[#9D7861] transition-shadow appearance-none cursor-pointer font-medium"
                    >
                      {availableModels.map(model => (
                        <option key={model.id} value={model.id}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-[#9D7861] pointer-events-none" size={16} />
                  </div>
                  <div className="flex items-start gap-2 mt-4 text-[#9D7861]/80 text-xs bg-[#9D7861]/5 p-3 rounded-lg border border-[#9D7861]/10">
                    <div className="shrink-0 mt-0.5"><Sparkles size={14} /></div>
                    <p>Changes apply immediately to new conversations. Choose the model that best fits your task complexity.</p>
                  </div>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="max-w-2xl space-y-8 animate-in slide-in-from-right-4 duration-500">
              <div className="text-center py-12 border-2 border-dashed border-[#d4c5b3] rounded-lg bg-[#fbf7e8]/50">
                <Sparkles size={32} className="mx-auto text-[#d4c5b3] mb-4" />
                <p className="text-[#9D7861] font-medium">Appearance settings coming soon...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ChatWorkspacePanel({ sessions, onNewChat, onSelectSession, onToggleJson }) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-6 pb-2">
        <h2 className="font-display font-bold text-xs text-gray-500 uppercase tracking-[0.2em] mb-4">Ryan Agent</h2>
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={onNewChat}
            className="flex-1 flex items-center gap-2 bg-emerald-600 text-white p-3 rounded-md shadow-md hover:bg-emerald-700 transition-all group"
          >
            <Plus size={18} />
            <span className="font-bold text-sm">New Chat</span>
          </button>
        </div>

      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
        <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 mt-4 px-2">Recent</div>
        {sessions.length === 0 && (
          <div className="px-2 text-xs text-gray-400 italic">No recent chats</div>
        )}
        {sessions.slice().reverse().map(session => (
          <div
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className="p-3 rounded-md bg-white border border-gray-100 hover:border-emerald-200 hover:bg-emerald-50/50 cursor-pointer transition-colors group shadow-sm"
          >
            <h4 className="text-sm font-bold text-gray-700 truncate">{session.title}</h4>
            <p className="text-xs text-gray-400 truncate mt-0.5">{new Date(session.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// --- Database Sidebar Component ---
function DatabaseSidebar({
  activeTab,
  setActiveTab,
  tableNames,
  expandedTables,
  toggleTable,
  fullSchema,
  handleTableClick,
  handleTableDoubleClick,
  onToggleJson
}) {
  // Icons
  const DatabaseIcon = ({ active }) => (
    <svg className={clsx("w-6 h-6 stroke-[1.5]", active ? "text-[#5a646a]" : "text-[#9D7861]")} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s8-1.79 8-4" />
    </svg>
  );
  const HistoryIcon = ({ active }) => (
    <svg className={clsx("w-6 h-6 stroke-[1.5]", active ? "text-[#5a646a]" : "text-[#9D7861] opacity-70")} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
  const CodeIcon = ({ active }) => (
    <svg className={clsx("w-6 h-6 stroke-[1.5]", active ? "text-[#5a646a]" : "text-[#9D7861] opacity-70")} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  );
  const ChevronRightIcon = ({ expanded, className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      className={clsx("w-3 h-3 transition-transform duration-200", expanded ? "rotate-90" : "", className)}>
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
  const TableIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 text-emerald-500">
      <path fillRule="evenodd" d="M1.5 5.25c0-.966.784-1.75 1.75-1.75h17.5c.966 0 1.75.784 1.75 1.75v13.5c0 .966-.784 1.75-1.75 1.75H3.25a1.75 1.75 0 0 1-1.75-1.75V5.25ZM3.25-.25a.25.25 0 0 0-.25.25v3.25h17.5V5.25a.25.25 0 0 0-.25-.25H3.25ZM3 10v7.75c0 .138.112.25.25.25h17.5a.25.25 0 0 0 .25-.25V10H3Z" clipRule="evenodd" />
    </svg>
  );
  const FolderIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 text-emerald-500">
      <path d="M19.5 21a3 3 0 0 0 3-3v-4.5a3 3 0 0 0-3-3h-15a3 3 0 0 0-3 3V18a3 3 0 0 0 3 3h15ZM1.5 10.146V6a3 3 0 0 1 3-3h5.379a2.25 2.25 0 0 1 1.59.659l2.122 2.121c.14.141.331.22.53.22H19.5a3 3 0 0 1 3 3v1.146A4.483 4.483 0 0 0 19.5 9h-15a4.483 4.483 0 0 0-3 1.146Z" />
    </svg>
  );

  return (
    <div className="flex h-full">
      {/* Rail */}
      <div className="w-14 bg-gray-50/50 border-r border-gray-200 flex flex-col items-center py-4 gap-4">
        <button onClick={() => setActiveTab('entities')} className="p-2 transition-transform hover:scale-105" title="Entities">
          <DatabaseIcon active={activeTab === 'entities'} />
        </button>
        <button onClick={() => setActiveTab('saved')} className="p-2 transition-transform hover:scale-105" title="Saved Queries">
          <CodeIcon active={activeTab === 'saved'} />
        </button>
        <button onClick={() => setActiveTab('history')} className="p-2 transition-transform hover:scale-105" title="History">
          <HistoryIcon active={activeTab === 'history'} />
        </button>
      </div>

      {/* Panel */}
      <div className="flex-1 flex flex-col bg-white">
        <div className="h-10 px-4 border-b border-gray-200 flex justify-between items-center bg-white">
          <div className="flex items-center gap-2">
            <button
              onClick={onToggleJson}
              className="p-1.5 text-gray-400 hover:bg-gray-100/10 rounded-lg transition-colors border border-gray-200"
              title="Toggle JSON Panel"
            >
              <Braces size={14} />
            </button>
            <h3 className="font-bold text-gray-600 text-xs tracking-wider uppercase">
              {activeTab === 'entities' && 'Entities'}
              {activeTab === 'saved' && 'Saved'}
              {activeTab === 'history' && 'History'}
            </h3>
            <span className="bg-emerald-50 text-emerald-700 text-[10px] px-1.5 rounded-full font-bold border border-emerald-100">{tableNames.length}</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-gray-200">
          {activeTab === 'entities' ? (
            <div className="space-y-0.5">
              {/* Mock DB Node */}
              <div className="pb-1 mb-1">
                <button className="flex items-center gap-1.5 w-full text-left px-2 py-1 hover:bg-emerald-50 rounded text-sm text-gray-700 font-medium group transition-colors">
                  <ChevronRightIcon expanded={true} className="text-gray-400 opacity-50" />
                  <FolderIcon />
                  <span>ryanrent.db</span>
                </button>
              </div>

              {tableNames.map(table => (
                <div key={table}>
                  <div className="flex items-center group">
                    <button onClick={() => toggleTable(table)} className="p-1 hover:bg-[#9D7861]/10 rounded text-[#9D7861]">
                      <ChevronRightIcon expanded={expandedTables[table]} />
                    </button>
                    <button
                      onClick={() => handleTableClick(table)}
                      onDoubleClick={() => handleTableDoubleClick && handleTableDoubleClick(table)}
                      className="flex-1 flex items-center gap-2 px-1 py-1 text-xs text-[#5a646a] hover:text-[#394348] hover:bg-[#9D7861]/5 rounded transition-colors text-left font-medium select-none"
                    >
                      <TableIcon />
                      <span className="truncate text-[13px]">{table}</span>
                    </button>
                  </div>

                  {/* Column Tree Expansion */}
                  {expandedTables[table] && (
                    <div className="ml-7 border-l border-[#e6dccb] pl-2 py-1 space-y-0.5">
                      {(fullSchema[table] || []).map(col => (
                        <div key={col.name} className="flex justify-between items-center text-[10px] py-0.5 pr-2 group/col hover:bg-[#9D7861]/5 rounded cursor-default">
                          <span className="text-[#394348] font-mono truncate">{col.name}</span>
                          <span className="text-[#9D7861]/70 italic">{col.type}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-[#9D7861]/50 text-xs italic">
              Empty
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// --- New Component: ThinkingProcess ---
function ThinkingProcess({ logs, isComplete }) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom of logs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="w-full px-4 mb-4">
      <div className="max-w-2xl bg-dark-panel border border-dark-border rounded-lg overflow-hidden">
        <div
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center justify-between p-3 cursor-pointer hover:bg-dark-bg/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">{isComplete ? "✅" : "⚙️"}</span>
            <span className="text-sm font-medium text-gray-300">
              {isComplete ? "Process Completed" : "Thinking Process..."}
            </span>
          </div>
          <ChevronRight
            size={16}
            className={clsx("text-dark-muted transition-transform", !isCollapsed && "rotate-90")}
          />
        </div>

        {!isCollapsed && (
          <div ref={scrollRef} className="bg-dark-bg p-3 max-h-60 overflow-y-auto space-y-1 text-xs font-mono border-t border-dark-border">
            {logs.map((log, idx) => (
              <div key={idx} className={clsx("break-words", log.is_error ? "text-red-400" : "text-gray-400")}>
                {log.content}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


// Helper to extract file path and render download link
function renderContentWithDownloads(content) {
  // Broadest regex: find any string ending in .xlsx that looks like a filename
  // This handles cases where the agent strips the path (e.g. "Bestandsnaam: file.xlsx")
  const fileRegex = /([a-zA-Z0-9_\-./\\:]+\.xlsx)/i;
  const match = content.match(fileRegex);

  if (match) {
    let fullPath = match[1];
    // clean up any leading/trailing punctuation if regex grabbed too much
    fullPath = fullPath.replace(/^['"`*]+|['"`*]+$/g, '');

    // Extract filename from path (works for both Unix and Windows paths)
    const filename = fullPath.split(/[/\\]/).pop();
    const downloadUrl = `http://localhost:8000/exports/${filename}`;

    return (
      <div className="space-y-4">
        <div className="whitespace-pre-wrap">{content}</div>
        <div className="bg-neutral-800/50 border border-neutral-700 rounded-lg p-4 flex items-center justify-between group hover:border-blue-500/50 transition-colors">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 group-hover:text-blue-300">
              <FileIcon className="w-6 h-6" />
            </div>
            <div>
              <div className="font-medium text-neutral-200">{filename}</div>
              <div className="text-sm text-neutral-500">Click to download</div>
            </div>
          </div>
          <a
            href={downloadUrl}
            download
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download
          </a>
        </div>
      </div>
    );
  }
  return <div className="whitespace-pre-wrap">{content}</div>;
}

function ChatMessage({ role, content, type, logs, isComplete }) {
  const isUser = role === 'user';

  if (type === 'thinking') {
    return <ThinkingProcess logs={logs} isComplete={isComplete} />;
  }

  const isError = type === 'error'; // Legacy error handling

  if (isError) {
    return (
      <div className="flex justify-center my-4">
        <span className="text-red-400 bg-red-400/10 px-3 py-1 rounded text-sm">{content}</span>
      </div>
    );
  }


  return (
    <div className={clsx(
      "flex w-full mb-8 px-2 animate-in fade-in slide-in-from-bottom-2 duration-500",
      isUser ? "justify-end" : "justify-start"
    )}>
      {!isUser && (
        <div className="mr-4 flex-shrink-0 mt-2">
          <Avatar name="Ryan" initials="R" color="bg-primary shadow-lg" />
        </div>
      )}
      <div className={clsx(
        "max-w-[85%] rounded-[2rem] px-8 py-6 shadow-sm text-[0.95rem] leading-relaxed tracking-wide font-medium transition-all hover:shadow-md",
        isUser
          ? "bg-primary text-white rounded-tr-sm shadow-primary/30"
          : "bg-white text-dark-text border border-gray-100 rounded-tl-sm"
      )}>
        {content && !isUser ? renderContentWithDownloads(content) : <div className="whitespace-pre-wrap font-sans">{content}</div>}
      </div>
      {isUser && (
        <div className="ml-4 flex-shrink-0 mt-2">
          <Avatar name="You" initials="Y" color="bg-dark-slate text-white bg-[#394348]" />
        </div>
      )}
    </div>
  );
}

function JsonSidePanel({ isOpen, onClose, data, tableName }) {
  const [editedJson, setEditedJson] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  // Initialize edited JSON when data changes
  useEffect(() => {
    if (data) {
      setEditedJson(JSON.stringify(data, null, 2));
    }
  }, [data]);

  const handleSave = async () => {
    if (!data || !tableName) return;

    setIsSaving(true);
    setSaveStatus(null);

    try {
      // Parse the edited JSON
      const parsedData = JSON.parse(editedJson);

      // Find the primary key (usually 'id' or first column)
      const primaryKey = Object.keys(data)[0]; // Assume first key is PK
      const primaryValue = data[primaryKey];

      // Build UPDATE query
      const setClauses = Object.entries(parsedData)
        .filter(([key]) => key !== primaryKey) // Don't update PK
        .map(([key, value]) => `${key} = ${typeof value === 'string' ? `'${value}'` : value}`)
        .join(', ');

      const updateQuery = `UPDATE ${tableName} SET ${setClauses} WHERE ${primaryKey} = ${typeof primaryValue === 'string' ? `'${primaryValue}'` : primaryValue}`;

      // Send to backend
      const res = await fetch("http://localhost:8000/api/sql/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql: updateQuery })
      });

      const result = await res.json();

      if (result.status === "error") {
        setSaveStatus({ type: 'error', message: result.error });
      } else {
        setSaveStatus({ type: 'success', message: 'Saved successfully!' });
        setTimeout(() => setSaveStatus(null), 2000);
      }
    } catch (err) {
      setSaveStatus({ type: 'error', message: err.message });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="w-96 border-l border-gray-200 bg-white flex flex-col shadow-md animate-in slide-in-from-right duration-300 rounded-[2rem] overflow-hidden border border-gray-100 h-full">
      <div className="h-10 border-b border-gray-200 flex items-center justify-between px-4 bg-gray-50">
        <div className="flex items-center gap-2 text-gray-500 font-bold">
          <Braces size={18} />
          <span className="uppercase tracking-wider text-xs">JSON Editor</span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-emerald-600 transition-colors">
          <X size={18} />
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        <textarea
          value={editedJson}
          onChange={(e) => setEditedJson(e.target.value)}
          className="w-full h-full bg-white border border-gray-200 rounded-md p-4 font-mono text-xs text-gray-700 resize-none shadow-inner outline-none focus:ring-2 focus:ring-emerald-500/20"
          spellCheck={false}
        />
      </div>
      <div className="p-4 border-t border-gray-200 bg-gray-50 space-y-2">
        {saveStatus && (
          <div className={`text-xs font-medium p-2 rounded ${saveStatus.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
            {saveStatus.message}
          </div>
        )}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="w-full py-2 bg-emerald-600 text-white rounded-md font-bold text-xs uppercase tracking-wider hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}

function InfoPanel({ isConnected }) {
  const [systemInfo, setSystemInfo] = useState({
    active_model: "Loading...",
    last_refreshed: null
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [sharedFiles, setSharedFiles] = useState([]);

  useEffect(() => {
    fetchSystemInfo();
    fetchFiles();
    const interval = setInterval(fetchFiles, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchFiles = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/files");
      const data = await res.json();
      setSharedFiles(data.files || []);
    } catch (err) {
      console.error("Failed to fetch files", err);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/system/status");
      const data = await res.json();
      setSystemInfo(data);
    } catch (err) {
      console.error("Failed to fetch system info", err);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch("http://localhost:8000/api/system/refresh", { method: 'POST' });
      const data = await res.json();
      setSystemInfo(prev => ({ ...prev, last_refreshed: data.last_refreshed }));
    } catch (err) {
      console.error("Refresh failed", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return "Never";
    return new Date(isoString).toLocaleString();
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="h-full flex flex-col bg-white text-gray-700">
      {/* Fixed Header Section: System Info - Flattened */}
      <div className="p-4 border-b border-gray-100 shrink-0 bg-white">
        <div className="flex items-center gap-3 mb-4">
          <Avatar name="Ryan Agent" initials="RA" active={isConnected} color="bg-emerald-600" />
          <div>
            <h3 className="font-bold text-sm text-gray-800">Ryan V2</h3>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <span className="flex items-center gap-1.5 text-[10px] text-green-600 font-bold bg-green-500/5 px-2 py-0.5 rounded-full ring-1 ring-green-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                  Online
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[10px] text-red-500 font-bold bg-red-500/5 px-2 py-0.5 rounded-full ring-1 ring-red-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  Offline
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-1.5 bg-gray-50 p-3 rounded-lg border border-gray-100">
          <div className="flex justify-between items-center text-[10px]">
            <span className="uppercase font-bold text-gray-400">Model</span>
            <span className="font-medium text-gray-700 truncate max-w-[140px]" title={systemInfo.active_model}>
              {systemInfo.active_model.split(':')[1] || systemInfo.active_model}
            </span>
          </div>
          <div className="flex justify-between items-center text-[10px]">
            <span className="uppercase font-bold text-gray-400">Synced</span>
            <div className="flex items-center gap-1.5">
              <span className="text-gray-700">{systemInfo.last_refreshed ? formatDate(systemInfo.last_refreshed).split(',')[0] : "Never"}</span>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className={clsx("text-gray-400 hover:text-emerald-600 transition-colors", isRefreshing && "animate-spin")}
              >
                <RotateCw size={10} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable List Section: Shared Files - Compact List */}
      <div className="flex-1 overflow-y-auto w-full">
        <div className="sticky top-0 bg-white/95 backdrop-blur-sm p-4 pb-2 flex justify-between items-center z-10 border-b border-gray-100">
          <h3 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Shared Files</h3>
          <button onClick={fetchFiles} className="text-emerald-600/50 hover:text-emerald-600 transition-colors">
            <RotateCw size={14} />
          </button>
        </div>

        <div className="p-2 space-y-0.5">
          {sharedFiles.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-[10px] text-[#9D7861]/40 italic">No files found</p>
            </div>
          ) : (
            sharedFiles.map((file, idx) => (
              <a
                key={idx}
                href={file.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-3 p-2 rounded-lg hover:bg-emerald-50 transition-all duration-200 border border-transparent hover:border-emerald-100"
                title={`${file.name} (${formatSize(file.size)})`}
              >
                <div className="shrink-0 text-emerald-600 opacity-70 group-hover:opacity-100">
                  {file.name.endsWith('.xlsx') ? <FileText size={18} /> : <FileIcon size={18} />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700 truncate leading-tight">{file.name}</p>
                  <p className="text-xs text-emerald-600/60 truncate">
                    {formatSize(file.size)} • {new Date(file.created * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <div className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Download size={16} className="text-emerald-600" />
                </div>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [activeView, setActiveView] = useState('chat'); // 'chat' or 'database'

  // --- Chat State ---
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '👋 Hallo! Ik ben Ryan V2.\nIk kan helpen met inspecties, contracten en het genereren van eindafrekeningen.\n\nWaar wil je mee beginnen?', type: 'text' }
  ]);
  const [input, setInput] = useState("");
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sessions, setSessions] = useState([]); // Array of {id, title, messages, updatedAt}
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const messagesEndRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // --- Layout State ---
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isJsonPanelOpen, setIsJsonPanelOpen] = useState(false);
  const [activeSettingsTab, setActiveSettingsTab] = useState('general'); // New Settings Tab State
  const [notifications, setNotifications] = useState([]);

  // --- Settings State ---
  const [availableModels, setAvailableModels] = useState([]);
  const [activeModel, setActiveModel] = useState("anthropic:claude-sonnet-4-5-20250929"); // Default

  // Load model from settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/settings");
        const data = await res.json();
        if (data.active_model) {
          setActiveModel(data.active_model);
        }
      } catch (err) {
        console.error("Failed to load settings", err);
      }
    };
    loadSettings();
  }, []);

  // Save model to API when changed
  const handleModelChange = async (modelId) => {
    setActiveModel(modelId);
    // Find the display label
    const model = availableModels.find(m => m.id === modelId);
    const displayName = model ? model.label : modelId;

    try {
      await fetch("http://localhost:8000/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          active_model: modelId,
          active_model_display: displayName
        })
      });
    } catch (err) {
      console.error("Failed to save settings", err);
    }
  };
  // Fetch models
  useEffect(() => {
    fetch("http://localhost:8000/api/config/models")
      .then(res => res.json())
      .then(data => {
        setAvailableModels(data.models);
        // Optionally set default if current invalid
      })
      .catch(err => console.error("Failed to fetch models", err));
  }, []);

  // --- Helpers ---
  const addNotification = (title) => {
    setNotifications(prev => [{ title, time: new Date().toLocaleTimeString() }, ...prev]);
  };

  // --- Chat Session Logic ---
  const saveCurrentSession = () => {
    const title = messages.find(m => m.role === 'user')?.content.slice(0, 30) + "..." || "New Conversation";
    const sessionData = {
      id: currentSessionId || Date.now(),
      title: title,
      messages: messages,
      updatedAt: Date.now()
    };

    setSessions(prev => {
      const exists = prev.find(s => s.id === sessionData.id);
      if (exists) {
        return prev.map(s => s.id === sessionData.id ? sessionData : s);
      }
      return [...prev, sessionData];
    });
  };

  const startNewChat = () => {
    if (messages.length > 1) {
      saveCurrentSession();
    }
    setMessages([{ role: 'assistant', content: '👋 Nieuwe chat gestart. Waarmee kan ik helpen?', type: 'text' }]);
    setCurrentSessionId(Date.now());
    // Re-connect WS to get fresh agent state (if backend supported session IDs per WS, detailed logic needed here, for now simple reset UX)
  };

  const loadSession = (sessionId) => {
    if (messages.length > 1) saveCurrentSession();
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setMessages(session.messages);
      setCurrentSessionId(session.id);
    }
  };


  // --- Database State (Lifted) ---
  const [fullSchema, setFullSchema] = useState({});
  const [dbActiveTab, setDbActiveTab] = useState('entities');
  const [expandedTables, setExpandedTables] = useState({});
  const [sharedQuery, setSharedQuery] = useState(""); // Shared with Explorer
  const [triggerExecute, setTriggerExecute] = useState(0); // Trigger execution in Explorer
  const [tableTabToOpen, setTableTabToOpen] = useState(null); // Signal to open a tab

  useEffect(() => {
    fetchSchema();
  }, []);

  const fetchSchema = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/schema");
      const data = await res.json();
      setFullSchema(data.schema || {});
    } catch (err) {
      console.error("Failed to fetch schema", err);
    }
  };

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  const handleTableClick = (tableName) => {
    // Single click: Just select for query (optional, maybe preview?)
    // For now we keep existing behavior or do nothing if Double Click is the primary action
    setSharedQuery(`SELECT * FROM ${tableName} LIMIT 50;`);
    // setTriggerExecute(prev => prev + 1); // logic moved to Tabs
  };

  const handleTableDoubleClick = (tableName) => {
    setTableTabToOpen(tableName);
    if (activeView !== 'database') {
      setActiveView('database');
      setIsSidebarOpen(true);
    }
  };

  // Reset tab signal after consumption
  const openTableTab = {
    tableName: tableTabToOpen,
    reset: () => setTableTabToOpen(null)
  };

  const [selectedJsonData, setSelectedJsonData] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null); // Track which table the row is from

  const handleViewSelect = (viewId) => {
    if (activeView === viewId) {
      // Toggle Sidebar if clicking active view
      setIsSidebarOpen(!isSidebarOpen);
    } else {
      // Switch view and ensure sidebar is open
      setActiveView(viewId);
      setIsSidebarOpen(true);
    }
  };

  const dbTableNames = Object.keys(fullSchema).sort();

  // ... (Keep Chat UseEffects) ...
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(() => { if (activeView === 'chat') scrollToBottom(); }, [messages, activeView]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws) ws.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [activeModel]); // Reconnect when model changes

  const connectWebSocket = () => {
    // Pass activeModel as query param
    const socket = new WebSocket(`ws://localhost:8000/ws/chat?model=${encodeURIComponent(activeModel)}`);

    socket.onopen = () => {
      console.log("Connected to Ryan Agent");
      setIsConnected(true);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'text') {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          // Append to existing assistant text bubble if not fixed
          if (last && last.role === 'assistant' && last.type === 'text' && !last.isFixed) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.content }];
          } else {
            return [...prev, { role: 'assistant', content: data.content, type: 'text' }];
          }
        });
      } else if (data.type === 'log') {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last && last.type === 'thinking' && !last.isComplete) {
            const newLogs = [...last.logs, { content: data.content, is_error: data.is_error }];
            return [...prev.slice(0, -1), { ...last, logs: newLogs }];
          } else {
            return [...prev, { role: 'assistant', type: 'thinking', logs: [{ content: data.content, is_error: data.is_error }], isComplete: false }];
          }
        });
      } else if (data.type === 'done') {
        setMessages(prev => {
          const newMessages = [...prev];
          for (let i = newMessages.length - 1; i >= 0; i--) {
            if (newMessages[i].type === 'thinking' && !newMessages[i].isComplete) {
              newMessages[i] = { ...newMessages[i], isComplete: true };
              break;
            }
          }
          return newMessages;
        });
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, { role: 'system', content: data.content, type: 'error' }]);
      }
    };

    socket.onclose = () => {
      console.log("Disconnected, retrying in 3s...");
      setIsConnected(false);
      setWs(null);
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket Error:", err);
      socket.close();
    };

    setWs(socket);
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: input, type: 'text' }]);
    const currentInput = input;
    setInput("");

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ message: currentInput }));
    } else {
      setMessages(prev => [...prev, { role: 'system', content: "⚠️ Offline. Reconnecting...", type: 'error' }]);
    }
  };

  return (
    <div className="flex h-screen bg-[#F7E5C1] text-[#394348] font-sans p-4 gap-4 overflow-hidden selection:bg-[#9D7861] selection:text-[#fbf7e8]">

      {/* 1. Global Rail (Floating Container) */}
      <div className="rounded-[2rem] overflow-hidden shadow-2xl border border-[#fbf7e8]/40 bg-[#eaddcf]/30 backdrop-blur-md flex h-full shrink-0">
        <GlobalRail
          activeView={activeView}
          onSelectView={handleViewSelect}
          notifications={notifications}
        />
      </div>

      {/* 2. Workspace Panel (Contextual - Collapsible) */}
      <div className={clsx(
        "bg-[#fbf7e8]/90 backdrop-blur-md rounded-[2rem] shadow-xl overflow-hidden border border-[#fbf7e8]/50 flex flex-col transition-all duration-300 ease-in-out shrink-0",
        isSidebarOpen ? "w-72 opacity-100 ml-0 translate-x-0" : "w-0 opacity-0 -ml-4 -translate-x-10 pointer-events-none"
      )}>
        {activeView === 'chat' && (
          <ChatWorkspacePanel
            sessions={sessions}
            onNewChat={startNewChat}
            onSelectSession={loadSession}
          />
        )}
        {activeView === 'database' && (
          <DatabaseSidebar
            activeTab={dbActiveTab}
            setActiveTab={setDbActiveTab}
            tableNames={dbTableNames}
            expandedTables={expandedTables}
            toggleTable={toggleTable}
            fullSchema={fullSchema}
            handleTableClick={handleTableClick}
            handleTableDoubleClick={handleTableDoubleClick}
            onToggleJson={() => setIsJsonPanelOpen(!isJsonPanelOpen)}
          />
        )}
        {activeView === 'settings' && (
          <SettingsSidebar
            activeTab={activeSettingsTab}
            setActiveTab={setActiveSettingsTab}
          />
        )}
      </div>

      {/* 3. Main Content Area */}
      <div className="flex-1 flex flex-row relative animate-in slide-in-from-bottom-4 duration-500 delay-100 gap-4">
        <div className="flex-1 flex flex-col h-full bg-[#fbf7e8] rounded-[2rem] shadow-xl overflow-hidden border border-[#fbf7e8]/50 relative">
          {activeView === 'chat' ? (
            <>
              {/* Chat Content */}
              <div className="h-20 border-b border-[#e6dccb] flex items-center justify-between px-8 bg-[#fbf7e8]/50 backdrop-blur-md z-10 sticky top-0">
                <div className="flex items-center gap-4">
                  <Avatar name="Ryan" initials="R" active={true} color="bg-[#9D7861] shadow-lg ring-2 ring-[#fbf7e8]" />
                  <div>
                    <h3 className="font-display font-bold text-lg text-[#394348] tracking-tight">Ryan V2</h3>
                    <div className="flex items-center gap-1.5">
                      <span className={clsx("w-2 h-2 rounded-full ring-2 ring-[#fbf7e8] transition-colors", isConnected ? "bg-green-500" : "bg-red-400")}></span>
                      <p className="text-xs text-[#9D7861] font-medium transition-opacity duration-300">
                        {isConnected ? "Online Assistant" : "Connecting..."}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-6 scroll-smooth bg-[#fbf7e8]">
                <div className="max-w-4xl mx-auto pt-4 pb-8">
                  {messages.map((m, i) => (
                    <ChatMessage key={i} {...m} />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Chat Input */}
              <div className="p-6 bg-[#fbf7e8]/80 backdrop-blur-sm border-t border-[#e6dccb]">
                <div className="max-w-4xl mx-auto relative">
                  <form onSubmit={sendMessage} className="relative group">
                    <div className="absolute inset-0 bg-[#9D7861]/5 rounded-lg transform transition-transform group-hover:scale-[1.01] duration-300"></div>
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Type to ask Ryan..."
                      className="relative w-full bg-[#fbf7e8] border border-[#e6dccb] rounded-lg p-5 pr-32 outline-none text-base placeholder-[#9D7861]/50 shadow-sm focus:ring-2 focus:ring-[#9D7861]/20 focus:border-[#9D7861] transition-all font-medium text-[#394348]"
                    />
                    <div className="absolute right-3 top-3 bottom-3 flex items-center gap-2">
                      <button type="button" className="p-2.5 text-[#9D7861]/70 hover:text-[#9D7861] hover:bg-[#9D7861]/10 transition-colors rounded-md">
                        <Paperclip size={20} />
                      </button>
                      <button type="submit" disabled={!input.trim()} className="p-2.5 bg-[#9D7861] text-[#fbf7e8] rounded-md hover:bg-[#7d5b46] transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:shadow-none transform active:scale-95">
                        <Send size={20} />
                      </button>
                    </div>
                  </form>
                  <div className="flex justify-center mt-3 gap-6">
                    <p className="text-xs font-medium text-dark-muted opacity-70">RyanRent AI • Powered by Claude 4.5</p>
                  </div>
                </div>
              </div>
            </>
          ) : activeView === 'database' ? (
            <DatabaseExplorer
              fullSchema={fullSchema}
              sharedQuery={sharedQuery}
              setSharedQuery={setSharedQuery}
              triggerExecute={triggerExecute}
              setTriggerExecute={setTriggerExecute}
              openTableTab={openTableTab}
              onToggleJson={() => setIsJsonPanelOpen(!isJsonPanelOpen)}
              onRowSelect={(row, tableName) => {
                setSelectedJsonData(row);
                setSelectedTable(tableName);
                setIsJsonPanelOpen(true);
              }}
            />
          ) : activeView === 'contracts' ? (
            <ContractWorkspace />
          ) : activeView === 'settings' ? (
            <SettingsWorkspace
              activeModel={activeModel}
              onModelChange={handleModelChange}
              availableModels={availableModels}
              activeTab={activeSettingsTab}
            />
          ) : null}
        </div>

        {/* JSON Side Panel (Inside Main Content) */}
        <JsonSidePanel
          isOpen={isJsonPanelOpen}
          onClose={() => setIsJsonPanelOpen(false)}
          data={selectedJsonData || { note: "Select a row to edit" }}
          tableName={selectedTable}
        />

        {/* 4. Floating Info Panel (Always Visible on XL screens for Chat) */}
        {activeView === 'chat' && (
          <div className="w-80 hidden xl:flex flex-col bg-[#fbf7e8] rounded-[2rem] shadow-xl overflow-hidden border border-[#e6dccb]/60">
            <InfoPanel isConnected={isConnected} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
