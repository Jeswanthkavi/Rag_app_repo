import React from 'react';
import { MessageSquare, LogIn, LogOut, ShieldCheck, FileText } from 'lucide-react';
import { User } from '@supabase/supabase-js';

interface NavbarProps {
  user: User | null;
  activeTab: 'chat' | 'documents';
  setActiveTab: (tab: 'chat' | 'documents') => void;
  onOpenAuth: () => void;
  onSignOut: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  activeTab,
  setActiveTab,
  onOpenAuth,
  onSignOut,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-slate-900 border border-teal-500/40 flex items-center justify-center p-1 shadow-md">
            <img src="/logo.png" alt="AK-RAG(18) Logo" className="h-8 w-8 object-contain rounded-lg" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">AK-RAG(18)</span>
              <span className="text-[10px] uppercase font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/40 px-2 py-0.5 rounded-full">
                Multi-Tenant
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Enterprise Document Grounding Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        {user && (
          <nav className="flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'chat'
                  ? 'bg-teal-500 text-slate-950 shadow-md font-semibold'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat Assistant</span>
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'documents'
                  ? 'bg-teal-500 text-slate-950 shadow-md font-semibold'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <FileText className="h-4 w-4" />
              <span>Documents</span>
            </button>
          </nav>
        )}

        {/* Tenant Profile / Auth Button */}
        <div className="flex items-center space-x-4">
          {user ? (
            <div className="flex items-center space-x-3">
              <div className="hidden md:flex flex-col text-right">
                <span className="text-xs font-medium text-slate-200">{user.email}</span>
                <span className="text-[10px] text-teal-400 flex items-center justify-end space-x-1">
                  <ShieldCheck className="h-3 w-3" />
                  <span>RLS Verified</span>
                </span>
              </div>
              <button
                onClick={onSignOut}
                title="Sign out"
                className="p-2 text-slate-400 hover:text-rose-400 bg-slate-800/40 hover:bg-rose-500/10 border border-slate-800 hover:border-rose-500/30 rounded-lg transition-all"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold bg-teal-500 hover:bg-teal-400 text-slate-950 shadow-lg shadow-teal-500/20 transition-all"
            >
              <LogIn className="h-4 w-4" />
              <span>Sign In / Register</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

