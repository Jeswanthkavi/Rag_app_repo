import React, { useState, useEffect } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from './lib/supabase';
import { Navbar } from './components/Navbar';
import { AuthModal } from './components/AuthModal';
import { DocumentManager } from './components/DocumentManager';
import { ChatInterface } from './components/ChatInterface';
import { CitationDrawer } from './components/CitationDrawer';
import { Citation } from './types';
import { Shield, Sparkles, FileText, Lock } from 'lucide-react';

export const App: React.FC = () => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [citationDrawerOpen, setCitationDrawerOpen] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  const handleInspectCitation = (citation: Citation) => {
    setSelectedCitation(citation);
    setCitationDrawerOpen(true);
  };

  const token = session?.access_token || '';

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-teal-500 selection:text-slate-950">
      <Navbar
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenAuth={() => setAuthModalOpen(true)}
        onSignOut={handleSignOut}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {user ? (
          <div>
            {activeTab === 'chat' ? (
              <ChatInterface
                token={token}
                onInspectCitation={handleInspectCitation}
              />
            ) : (
              <DocumentManager token={token} />
            )}
          </div>
        ) : (
          /* Unauthenticated Landing / Call to Action */
          <div className="py-12 flex flex-col items-center justify-center text-center max-w-3xl mx-auto space-y-8">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/30">
              <Sparkles className="h-3.5 w-3.5 text-teal-400" />
              <span>Production-Grade Multi-Tenant RAG</span>
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
                Grounded Document Intelligence with{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-400">
                  Verifiable Citations
                </span>
              </h1>
              <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
                Experience zero-hallucination question answering. Every factual response is cryptographically
                isolated by Supabase Row Level Security (RLS) and bound to exact document page numbers.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full max-w-md">
              <button
                onClick={() => setAuthModalOpen(true)}
                className="w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 shadow-xl shadow-teal-500/25 transition-all"
              >
                Sign In to Workspace
              </button>
            </div>

            {/* Architecture Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-10 text-left w-full">
              <div className="bg-slate-900/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                <div className="h-10 w-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20">
                  <Shield className="h-5 w-5" />
                </div>
                <h4 className="font-bold text-sm text-white">Strict Multi-Tenant RLS</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  PostgreSQL 15+ Row Level Security guarantees data isolation with `auth.uid() = user_id`.
                </p>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                <div className="h-10 w-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20">
                  <FileText className="h-5 w-5" />
                </div>
                <h4 className="font-bold text-sm text-white">Verifiable Page Citations</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Layout-aware PDF parsing preserves exact page boundaries and renders clickable audit pills.
                </p>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                <div className="h-10 w-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20">
                  <Lock className="h-5 w-5" />
                </div>
                <h4 className="font-bold text-sm text-white">Anti-Hallucination Guardrails</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Strict LLM system instructions enforce unequivocal refusal when source passages lack ground truth.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Interactive Citation Drawer */}
      <CitationDrawer
        isOpen={citationDrawerOpen}
        citation={selectedCitation}
        onClose={() => setCitationDrawerOpen(false)}
      />

      {/* Supabase Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={() => {}}
      />
    </div>
  );
};

export default App;

