import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Database, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const EXAMPLE_QUERIES = [
  "What is the average asset cost?",
  "How many invoices are from Maharashtra?",
  "Show top tractor models by count",
  "Which dealers sell Mahindra tractors?",
  "What is the total portfolio value?",
  "Find invoices with horse power above 50 HP",
];

const PortfolioChat = ({ onSendQuery }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (queryText) => {
    const query = queryText || input.trim();
    if (!query || isLoading) return;

    const userMsg = { role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await onSendQuery(query);
      const assistantMsg = {
        role: 'assistant',
        content: response.answer || 'No response received.',
        sources: response.sources || [],
        queryType: response.query_type || 'unknown',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to get response'}`,
        sources: [],
        isError: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full min-h-[600px] bg-finance-dark/60 rounded-2xl border border-green-500/20 overflow-hidden backdrop-blur-md">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-green-400/40 to-green-600/20 border-b border-green-500/20 flex items-center gap-3">
        <div className="p-2 bg-green-500/20 rounded-xl border border-green-500/30">
          <MessageSquare className="w-5 h-5 text-agri-accent" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Portfolio Intelligence</h3>
          <p className="text-[11px] text-green-400/60">Ask questions about your invoice portfolio</p>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-full text-center py-10"
          >
            <div className="p-4 bg-green-500/10 rounded-2xl border border-green-500/20 mb-5">
              <Sparkles className="w-10 h-10 text-agri-accent" />
            </div>
            <h4 className="text-lg font-bold text-gray-200 mb-2">Ask KrishiIntel AI</h4>
            <p className="text-sm text-gray-500 max-w-md mb-6">
              Query your portfolio of invoices using natural language. Get instant insights on costs, models, dealers, and more.
            </p>
            <div className="flex flex-wrap gap-2 max-w-lg justify-center">
              {EXAMPLE_QUERIES.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  className="px-3 py-1.5 text-xs bg-finance-dark border border-finance-dark rounded-full text-gray-400 hover:text-green-400 hover:border-green-500/40 transition-all hover:bg-green-400/20"
                >
                  {q}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-green-500/20 border border-green-500/30 flex items-center justify-center mt-1">
                  <Bot className="w-4 h-4 text-agri-accent" />
                </div>
              )}
              <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-1' : ''}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${msg.role === 'user'
                    ? 'bg-green-400/30 border border-green-500/30 text-green-400'
                    : msg.isError
                      ? 'bg-red-900/20 border border-red-500/30 text-red-200'
                      : 'bg-finance-dark/80 border border-finance-dark text-gray-200'
                    }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                {/* Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5 px-1">
                    <Database className="w-3 h-3 text-gray-500 mt-0.5" />
                    {msg.sources.map((src, j) => (
                      <span
                        key={j}
                        className="text-[10px] font-mono px-2 py-0.5 bg-finance-dark border border-finance-dark rounded-full text-gray-400"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                )}
                {/* Query type badge */}
                {msg.queryType && msg.role === 'assistant' && (
                  <div className="mt-1.5 px-1">
                    <span className={`text-[9px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full ${msg.queryType === 'sql'
                      ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-500/30'
                      : 'bg-green-600/30 text-green-300 border border-agri-accent/30'
                      }`}>
                      {msg.queryType === 'sql' ? '⚡ SQL Query' : '🧠 RAG + AI'}
                    </span>
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-agri-accent/20 border border-agri-accent/30 flex items-center justify-center mt-1 order-2">
                  <User className="w-4 h-4 text-green-300" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-green-500/20 border border-green-500/30 flex items-center justify-center">
              <Bot className="w-4 h-4 text-agri-accent animate-pulse" />
            </div>
            <div className="bg-finance-dark/80 border border-finance-dark rounded-2xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-agri-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-agri-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-agri-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-green-500/20 bg-finance-dark/60">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your invoice portfolio..."
            disabled={isLoading}
            className="flex-1 bg-finance-dark/80 border border-finance-dark rounded-xl px-4 py-3 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/30 transition-all disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="px-4 py-3 bg-gradient-to-r from-green-400 to-green-500 hover:from-green-500 hover:to-agri-accent text-white rounded-xl transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(14,165,233,0.2)] hover:shadow-[0_0_20px_rgba(14,165,233,0.4)]"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PortfolioChat;
