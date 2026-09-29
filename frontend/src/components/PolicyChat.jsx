import React, { useState } from 'react';
import { askQuestion } from '../services/api';

const PolicyChat = ({ activePolicy }) => {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  if (!activePolicy) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-xl text-center">
        <p className="text-yellow-700 font-medium">⚠️ Please upload or select a policy first.</p>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const q = question.trim();
    setQuestion('');
    
    // Add user message to history
    const userMsg = { role: 'user', text: q };
    setHistory((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await askQuestion(activePolicy.policy_id, q);
      const botMsg = {
        role: 'bot',
        text: data.answer,
        citations: data.citations || [],
        disclaimer: data.disclaimer
      };
      setHistory((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error(error);
      const errorMsg = { role: 'bot', text: 'Sorry, I encountered an error. Make sure the backend is reachable.' };
      setHistory((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[70vh] bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="bg-gray-50 border-b border-gray-100 p-4">
        <h2 className="font-bold text-gray-800">Chat with Policy: <span className="text-indigo-600 font-medium">{activePolicy.filename}</span></h2>
      </div>
      
      <div className="flex-grow overflow-y-auto p-4 space-y-6">
        {history.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            <p>Ask a question about this policy!</p>
            <p className="text-sm mt-2">Example: "What is my deductible?" or "Are dental implants covered?"</p>
          </div>
        )}
        
        {history.map((msg, index) => (
          <div key={index} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-5 py-3 shadow-sm ${
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-tr-none' 
                : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
            }`}>
              <div className="whitespace-pre-wrap leading-relaxed text-sm md:text-base">{msg.text}</div>
              
              {msg.role === 'bot' && msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <p className="text-xs font-semibold text-gray-500 mb-2">CITATIONS:</p>
                  <div className="flex flex-col gap-2">
                    {msg.citations.map((cite, i) => (
                      <div key={i} className="bg-gray-50 rounded p-2 text-xs text-gray-600 border border-gray-100 flex gap-2">
                        <span className="bg-indigo-100 text-indigo-700 font-bold px-1.5 py-0.5 rounded text-[10px] whitespace-nowrap h-fit">
                          Pg {cite.page_number}
                        </span>
                        <span className="italic line-clamp-3 leading-snug">"{cite.text}"</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {msg.role === 'bot' && msg.disclaimer && (
                <div className="mt-3 text-[10px] text-gray-400 italic">
                  {msg.disclaimer}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 border border-gray-200 rounded-2xl rounded-tl-none px-5 py-3 text-gray-500 flex items-center gap-2 shadow-sm">
              <span className="animate-pulse">●</span>
              <span className="animate-pulse animation-delay-200">●</span>
              <span className="animate-pulse animation-delay-400">●</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about coverage, limits, out-of-pocket costs..."
            className="flex-grow border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!question.trim() || loading}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <span>Send</span> 🚀
          </button>
        </form>
      </div>
    </div>
  );
};

export default PolicyChat;
