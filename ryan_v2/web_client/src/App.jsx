import React, { useState, useEffect, useRef } from 'react';
import { Send, Menu, Settings, Bell, User, Paperclip, Mic, FileText, ChevronRight, Hash, MessageSquare, Plus } from 'lucide-react';
import clsx from 'clsx';

// --- Components ---

function Avatar({ name, initials, active, color }) {
  return (
    <div className="relative">
      <div className={clsx("w-10 h-10 rounded-full flex items-center justify-center text-white font-medium text-sm", color || "bg-blue-500")}>
        {initials || name.slice(0, 2).toUpperCase()}
      </div>
      {active && <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-dark-panel rounded-full"></div>}
    </div>
  );
}

function Sidebar({ activeSession, onSelectSession }) {
  const contacts = [
    { id: 1, name: "Ryan Agent (V2)", role: "RyanRent AI", status: "Active", time: "Now", badge: 1, color: "bg-blue-600" },
    { id: 2, name: "Historical Archive", role: "Past Sessions", status: "Offline", time: "Yesterday", badge: 0, color: "bg-purple-600" },
  ];

  return (
    <div className="w-80 border-r border-dark-border flex flex-col bg-dark-panel h-screen">
      <div className="p-5">
        <div className="flex bg-dark-bg rounded-lg p-2 items-center gap-2 border border-dark-border focus-within:border-primary transition-colors">
          <Menu size={18} className="text-dark-muted" />
          <input
            className="bg-transparent outline-none flex-1 text-sm placeholder-dark-muted"
            placeholder="Search..."
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 space-y-2">
        {contacts.map(c => (
          <div
            key={c.id}
            onClick={() => onSelectSession(c.id)}
            className={clsx(
              "flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all",
              activeSession === c.id ? "bg-dark-bg border border-dark-border shadow-sm" : "hover:bg-dark-bg/50"
            )}
          >
            <Avatar name={c.name} initials={c.name[0]} active={c.status === "Active"} color={c.color} />
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-start">
                <h4 className="text-sm font-semibold truncate">{c.name}</h4>
                <span className="text-xs text-dark-muted whitespace-nowrap">{c.time}</span>
              </div>
              <p className="text-xs text-dark-muted truncate mt-0.5">{c.role}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function InfoPanel() {
  return (
    <div className="w-80 border-l border-dark-border bg-dark-panel h-screen overflow-y-auto hidden xl:block">
      <div className="p-6 border-b border-dark-border">
        <div className="flex justify-between items-start mb-4">
          <h2 className="font-semibold text-lg">General Info</h2>
          <ChevronRight size={18} className="text-dark-muted" />
        </div>
        <div className="bg-dark-bg rounded-xl p-4 border border-dark-border">
          <div className="flex items-center gap-3 mb-3">
            <Avatar name="Ryan Agent" initials="RA" color="bg-blue-600" />
            <div>
              <h3 className="font-medium text-sm">Ryan V2</h3>
              <p className="text-xs text-dark-muted">AI Property Assistant</p>
            </div>
          </div>
          <div className="space-y-3 mt-4">
            <div>
              <p className="text-xs text-dark-muted uppercase font-semibold mb-1">Status</p>
              <span className="bg-green-500/10 text-green-500 text-xs px-2 py-1 rounded font-medium">Active</span>
            </div>
            <div>
              <p className="text-xs text-dark-muted uppercase font-semibold mb-1">Version</p>
              <p className="text-sm">2.1.0 (Beta)</p>
            </div>
            <div>
              <p className="text-xs text-dark-muted uppercase font-semibold mb-1">Capabilities</p>
              <div className="flex flex-wrap gap-1">
                {['Database', 'Calculator', 'Contracts'].map(tag => (
                  <span key={tag} className="bg-dark-panel border border-dark-border text-xs px-2 py-0.5 rounded text-dark-muted">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        <h3 className="text-sm font-semibold text-dark-muted mb-4 uppercase tracking-wider">Shared Files</h3>
        <div className="space-y-3">
          <div className="bg-blue-500/10 p-3 rounded-lg flex items-center gap-3 cursor-pointer hover:bg-blue-500/20 transition-colors">
            <div className="p-2 bg-blue-500/20 rounded text-blue-400">
              <FileText size={18} />
            </div>
            <div>
              <p className="text-sm font-medium">Eindafrekening_V1.pdf</p>
              <p className="text-xs text-dark-muted">234 KB • Just now</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- New Component: ThinkingProcess ---
function ThinkingProcess({ logs, isComplete }) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const scrollRef = useRef(null);

  // Auto-expand on new logs if not explicitly collapsed by user (optional refinement)
  // For now, default collapsed like TUI

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


function ChatMessage({ role, content, type, logs, isComplete }) {
  const isUser = role === 'user';

  // Special handling for Thinking Process
  if (type === 'thinking') {
    return <ThinkingProcess logs={logs} isComplete={isComplete} />;
  }

  const isError = type === 'error'; // Legacy error handling if needed, but errors now come as logs usually

  if (isError) {
    return (
      <div className="flex justify-center my-4">
        <span className="text-red-400 bg-red-400/10 px-3 py-1 rounded text-sm">{content}</span>
      </div>
    );
  }

  return (
    <div className={clsx("flex w-full mb-6 px-4", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="mr-3 flex-shrink-0 mt-1">
          <Avatar name="Ryan" initials="R" color="bg-blue-600" />
        </div>
      )}
      <div className={clsx(
        "max-w-2xl px-5 py-3 shadow-sm text-sm leading-relaxed",
        isUser
          ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm"
          : "bg-dark-panel border border-dark-border rounded-2xl rounded-tl-sm text-gray-200"
      )}>
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
      {isUser && (
        <div className="ml-3 flex-shrink-0 mt-1">
          <Avatar name="You" initials="Y" color="bg-dark-border" />
        </div>
      )}
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '👋 Hallo! Ik ben Ryan V2.\nIk kan helpen met inspecties, contracten en het genereren van eindafrekeningen.\n\nWaar wil je mee beginnen?', type: 'text' }
  ]);
  const [input, setInput] = useState("");
  const [activeSession, setActiveSession] = useState(1);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Connect to backend WebSocket
    const socket = new WebSocket("ws://localhost:8000/ws/chat");

    socket.onopen = () => {
      console.log("Connected to Ryan Agent");
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'text') {
        setMessages(prev => {
          // If the last message was a "Thinking Process" that is complete, start a new text message
          // If the last message was text from assistant, append to it
          const last = prev[prev.length - 1];
          if (last && last.role === 'assistant' && last.type === 'text' && !last.isFixed) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.content }];
          } else {
            return [...prev, { role: 'assistant', content: data.content, type: 'text' }];
          }
        });
      }
      else if (data.type === 'log') {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          // If we already have a thinking block at the end, append log
          if (last && last.type === 'thinking' && !last.isComplete) {
            const newLogs = [...last.logs, { content: data.content, is_error: data.is_error }];
            return [...prev.slice(0, -1), { ...last, logs: newLogs }];
          } else {
            // Start a new thinking block
            return [...prev, {
              role: 'assistant',
              type: 'thinking',
              logs: [{ content: data.content, is_error: data.is_error }],
              isComplete: false
            }];
          }
        });
      }
      else if (data.type === 'done') {
        setMessages(prev => {
          // Mark the last thinking block as complete if it exists
          // Also mark last text as 'fixed' so new text starts new bubble if needed (though usually done means stream end)
          const newMessages = [...prev];

          // Find last thinking block
          for (let i = newMessages.length - 1; i >= 0; i--) {
            if (newMessages[i].type === 'thinking' && !newMessages[i].isComplete) {
              newMessages[i] = { ...newMessages[i], isComplete: true };
              break;
            }
          }
          // Find last textual message to fallback isFixed logic if you want 
          // (not strictly necessary with current logic but good practice)

          return newMessages;
        });
      }
      else if (data.type === 'error') {
        // Legacy error or top-level system error
        setMessages(prev => [...prev, { role: 'system', content: data.content, type: 'error' }]);
      }
    };

    socket.onclose = () => console.log("Disconnected");
    setWs(socket);

    return () => socket.close();
  }, []);

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim() || !ws) return;

    setMessages(prev => [...prev, { role: 'user', content: input, type: 'text' }]);
    ws.send(JSON.stringify({ message: input }));
    setInput("");
  };

  return (
    <div className="flex h-screen bg-dark-bg text-dark-text font-sans overflow-hidden">
      {/* Sidebar */}
      <Sidebar activeSession={activeSession} onSelectSession={setActiveSession} />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-dark-bg relative">
        {/* Header */}
        <div className="h-16 border-b border-dark-border flex items-center justify-between px-6 bg-dark-bg/80 backdrop-blur-sm z-10 sticky top-0">
          <div className="flex items-center gap-3">
            <Avatar name="Ryan" initials="R" active={true} color="bg-blue-600" />
            <div>
              <h3 className="font-semibold text-sm">Ryan V2</h3>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                <p className="text-xs text-dark-muted">Online</p>
              </div>
            </div>
          </div>
          <div className="flex gap-4 text-dark-muted">
            <Bell size={20} className="hover:text-white cursor-pointer" />
            <Settings size={20} className="hover:text-white cursor-pointer" />
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
          <div className="max-w-3xl mx-auto pt-4">
            {messages.map((m, i) => (
              <ChatMessage key={i} {...m} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-6">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={sendMessage} className="relative bg-dark-panel border border-dark-border rounded-2xl shadow-lg focus-within:ring-2 focus-within:ring-blue-500/50 transition-all">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="w-full bg-transparent p-4 pr-32 outline-none text-sm placeholder-dark-muted"
              />
              <div className="absolute right-2 top-2 bottom-2 flex items-center gap-1">
                <button type="button" className="p-2 text-dark-muted hover:text-white transition-colors rounded-lg hover:bg-dark-border/50">
                  <Paperclip size={18} />
                </button>
                <button type="submit" className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors shadow-md">
                  <Send size={18} />
                </button>
              </div>
            </form>
            <p className="text-center text-xs text-dark-muted mt-3">RyanRent AI can make mistakes. Verify important info.</p>
          </div>
        </div>
      </div>

      {/* Right Info Panel */}
      <InfoPanel />
    </div>
  );
}

export default App;
