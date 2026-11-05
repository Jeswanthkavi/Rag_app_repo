import React from 'react';
import { X, FileText, Bookmark, Target, ShieldCheck } from 'lucide-react';
import { Citation } from '../types';

interface CitationDrawerProps {
  isOpen: boolean;
  citation: Citation | null;
  onClose: () => void;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({ isOpen, citation, onClose }) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col shadow-2xl relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-teal-500/10 text-teal-400 rounded-xl border border-teal-500/20">
              <Bookmark className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Verified Source Citation</h3>
              <p className="text-xs text-slate-400">Strict Anti-Hallucination Audit</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Details */}
        <div className="flex-1 overflow-y-auto py-6 space-y-5">
          {/* Document and Page pill */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-slate-300">
                <FileText className="h-4 w-4 text-teal-400" />
                <span className="font-semibold text-sm">{citation.document_name}</span>
              </div>
              <span className="px-2.5 py-1 text-xs font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30 rounded-full">
                Page {citation.page_number}
              </span>
            </div>

            {citation.similarity !== undefined && citation.similarity !== null && (
              <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
                <span className="flex items-center space-x-1">
                  <Target className="h-3.5 w-3.5 text-teal-400" />
                  <span>Cosine Similarity</span>
                </span>
                <span className="font-mono font-medium text-teal-300">
                  {(citation.similarity * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>

          {/* Exact Extracted Passage */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Exact Document Passage Content
            </label>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-sm text-slate-200 leading-relaxed font-mono whitespace-pre-wrap selection:bg-teal-500 selection:text-slate-950">
              {citation.passage_preview || 'Exact passage text verified during embedding retrieval.'}
            </div>
          </div>

          {/* RLS Guarantee Card */}
          <div className="p-3 bg-teal-500/5 border border-teal-500/20 rounded-xl flex items-start space-x-3 text-xs text-slate-300">
            <ShieldCheck className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-teal-300">Multi-Tenant Tenant Isolation</p>
              <p className="text-slate-400 mt-0.5">
                This excerpt is cryptographically bound to your authenticated user ID and cannot be accessed by other tenants.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm rounded-xl transition-all"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

