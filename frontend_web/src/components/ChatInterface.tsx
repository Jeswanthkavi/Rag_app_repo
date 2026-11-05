import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, Bot, User as UserIcon, Bookmark, Sparkles, Loader2, ArrowRight } from 'lucide-react';
import { Message, Conversation, Citation } from '../types';
import { listConversations, getConversationMessages, sendChatMessageStream } from '../lib/api';

interface ChatInterfaceProps {
  token: string;
  onInspectCitation: (citation: Citation) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ token, onInspectCitation }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamedText]);

  // Load user conversations
  const loadConversations = async () => {
    try {
      const convs = await listConversations(token);
      setConversations(convs);
      if (convs.length > 0 && !activeConvId) {
        setActiveConvId(convs[0].id);
      }
    } catch {
      // Ignore initial load if empty
    }
  };

  useEffect(() => {
    loadConversations();
  }, [token]);

  // Load messages when activeConvId changes
  useEffect(() => {
    if (!activeConvId) {
      setMessages([]);
      return;
    }
    const loadMessages = async () => {
      try {
        const msgs = await getConversationMessages(activeConvId, token);
        setMessages(msgs);
      } catch {
        // Handle error
      }
    };
    loadMessages();
  }, [activeConvId, token]);

  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
    setInputMessage('');
    setStreamedText('');
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || streaming) return;

    const query = inputMessage.trim();
    setInputMessage('');

    // Append user message optimistically
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConvId || 'pending',
      sender: 'user',
      content: query,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    setStreaming(true);
    setStreamedText('');

    let accumulatedAnswer = '';

    await sendChatMessageStream(
      token,
      {
        conversation_id: activeConvId,
        message: query,
      },
      (tokenChunk) => {
        accumulatedAnswer += tokenChunk;
        setStreamedText(accumulatedAnswer);
      },
      (donePayload) => {
        setStreaming(false);
        setStreamedText('');

        const finalMsg: Message = {
          id: `bot-${Date.now()}`,
          conversation_id: donePayload.conversation_id || activeConvId || 'new',
          sender: 'assistant',
          content: donePayload.answer,
          citations: donePayload.citations || [],
          created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, finalMsg]);
        loadConversations();
      },
      (errorDetail) => {
        setStreaming(false);
        setStreamedText('');
        alert(`Chat Error: ${errorDetail}`);
      }
    );
  };

  // Helper to render text with clickable citation badges
  const renderMessageContent = (content: string, citations: Citation[]) => {
    const citationRegex = /\[([^,\]]+?),\s*Page\s*(\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(content)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        parts.push(content.substring(lastIndex, matchIndex));
      }

      const docName = match[1].trim();
      const pageNum = parseInt(match[2].trim(), 10);

      // Match against citations array if present
      const matchedCitation =
        citations.find(
          (c) =>
            (c.document_name.toLowerCase().includes(docName.toLowerCase()) ||
              docName.toLowerCase().includes(c.document_name.toLowerCase())) &&
            c.page_number === pageNum
        ) || {
          document_name: docName,
          page_number: pageNum,
          passage_preview: `Passage from ${docName} on Page ${pageNum}`,
        };

      parts.push(
        <button
          key={`cit-${matchIndex}`}
          onClick={() => onInspectCitation(matchedCitation)}
          className="inline-flex items-center space-x-1 mx-1 px-2 py-0.5 rounded-md text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-400 hover:text-slate-950 transition-all cursor-pointer shadow-sm align-middle"
          title={`Click to inspect verified source from ${docName}, Page ${pageNum}`}
        >
          <Bookmark className="h-3 w-3 text-amber-400" />
          <span>{docName}, P.{pageNum}</span>
        </button>
      );

      lastIndex = matchIndex + match[0].length;
    }

    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    return (
      <div className="space-y-2">
        <div className="whitespace-pre-wrap leading-relaxed">{parts}</div>
        {citations && citations.length > 0 && (
          <div className="pt-2 mt-2 border-t border-slate-800/80 flex flex-wrap gap-1.5 items-center">
            <span className="text-[11px] text-slate-500 font-medium">Verified Sources:</span>
            {citations.map((c, i) => (
              <button
                key={i}
                onClick={() => onInspectCitation(c)}
                className="text-[11px] px-2 py-0.5 bg-slate-800 hover:bg-amber-500/20 text-slate-300 hover:text-amber-300 border border-slate-700 hover:border-amber-500/40 rounded-full flex items-center space-x-1 transition-all"
              >
                <span>{c.document_name}</span>
                <span className="text-amber-400 font-semibold">P.{c.page_number}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)]">
      {/* Sidebar - Sessions */}
      <div className="hidden lg:flex flex-col bg-slate-900/60 border border-slate-800 rounded-2xl p-4 overflow-hidden">
        <button
          onClick={handleNewChat}
          className="w-full py-2.5 px-4 rounded-xl font-semibold text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 flex items-center justify-center space-x-2 shadow-lg shadow-teal-500/20 transition-all mb-4"
        >
          <Plus className="h-4 w-4" />
          <span>New RAG Chat</span>
        </button>

        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 px-1">
          Recent Conversations
        </span>

        <div className="flex-1 overflow-y-auto space-y-1 pr-1">
          {conversations.length === 0 ? (
            <p className="text-xs text-slate-500 italic p-2">No prior conversations found.</p>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setActiveConvId(conv.id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition-all truncate flex items-center justify-between ${
                  activeConvId === conv.id
                    ? 'bg-slate-800 text-teal-300 border border-teal-500/30 font-medium'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <span className="truncate">{conv.title}</span>
                <ArrowRight className="h-3 w-3 opacity-40 shrink-0 ml-1" />
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="lg:col-span-3 flex flex-col bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        {/* Chat Header */}
        <div className="px-6 py-3.5 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 bg-teal-500/10 text-teal-400 rounded-lg border border-teal-500/20">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white tracking-tight">Personal Document Assistant</h4>
              <p className="text-[11px] text-slate-400">Grounded exclusively on your uploaded documents</p>
            </div>
          </div>
          <button
            onClick={handleNewChat}
            className="lg:hidden p-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg flex items-center space-x-1"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New</span>
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.length === 0 && !streaming && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-3">
              <div className="h-14 w-14 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center">
                <Bot className="h-7 w-7" />
              </div>
              <h4 className="text-base font-bold text-white">Ask your documents anything</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Every response strictly cites source document names and exact page numbers. If facts are absent,
                anti-hallucination guardrails guarantee strict refusal.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="h-8 w-8 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-md ${
                  msg.sender === 'user'
                    ? 'bg-teal-500 text-slate-950 font-medium rounded-tr-sm ml-auto'
                    : 'bg-slate-950/80 border border-slate-800 text-slate-200 rounded-tl-sm'
                }`}
              >
                {msg.sender === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  renderMessageContent(msg.content, msg.citations)
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="h-8 w-8 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {/* Streaming Bubble */}
          {streaming && (
            <div className="flex items-start space-x-3">
              <div className="h-8 w-8 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
              <div className="max-w-[85%] rounded-2xl rounded-tl-sm p-4 text-sm bg-slate-950/80 border border-slate-800 text-slate-200 shadow-md">
                <p className="whitespace-pre-wrap">{streamedText}</p>
                <div className="inline-block w-2 h-4 bg-teal-400 ml-1 animate-pulse" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-800 bg-slate-950/60">
          <div className="relative flex items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask a question grounded in your documents..."
              disabled={streaming}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-4 pr-12 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={streaming || !inputMessage.trim()}
              className="absolute right-2 p-2 bg-teal-500 hover:bg-teal-400 disabled:opacity-40 text-slate-950 rounded-lg transition-all"
            >
              {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

