import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, FileText, Trash2, CheckCircle2, AlertCircle, Loader2, RefreshCw, FileCode } from 'lucide-react';
import { DocumentItem } from '../types';
import { listDocuments, uploadDocument, deleteDocument, getDocumentStatus } from '../lib/api';

interface DocumentManagerProps {
  token: string;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({ token }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    try {
      setErrorMsg(null);
      const docs = await listDocuments(token);
      setDocuments(docs);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [token]);

  // Polling mechanism for documents in pending or processing state
  useEffect(() => {
    const processingDocs = documents.filter((d) => d.status === 'pending' || d.status === 'processing');
    if (processingDocs.length === 0) return;

    const interval = setInterval(async () => {
      let anyChanged = false;
      const updatedDocs = await Promise.all(
        documents.map(async (doc) => {
          if (doc.status === 'pending' || doc.status === 'processing') {
            try {
              const statusData = await getDocumentStatus(doc.id, token);
              if (statusData.status !== doc.status) {
                anyChanged = true;
                return {
                  ...doc,
                  status: statusData.status as any,
                  page_count: statusData.page_count,
                  error_message: statusData.error_message,
                };
              }
            } catch {
              // Ignore polling errors
            }
          }
          return doc;
        })
      );

      if (anyChanged) {
        setDocuments(updatedDocs);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [documents, token]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    // Check extension
    const name = file.name.toLowerCase();
    if (!name.endsWith('.pdf') && !name.endsWith('.txt') && !name.endsWith('.md')) {
      setErrorMsg('Please upload a valid .pdf, .txt, or .md document.');
      return;
    }

    setUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);
    setErrorMsg(null);

    try {
      const newDoc = await uploadDocument(file, token);
      setDocuments((prev) => [newDoc, ...prev]);
      setUploadProgress(null);
    } catch (err: any) {
      setErrorMsg(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete "${name}" and all its vector embeddings?`)) {
      return;
    }

    try {
      await deleteDocument(id, token);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-teal-500 bg-teal-500/10 scale-[1.01]'
            : 'border-slate-800 hover:border-teal-500/50 bg-slate-900/40 hover:bg-slate-900/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="h-14 w-14 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center mx-auto mb-3">
          {uploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <UploadCloud className="h-6 w-6" />}
        </div>
        <h4 className="text-base font-bold text-white tracking-tight">
          {uploading ? uploadProgress : 'Drop documents here or click to browse'}
        </h4>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Supports multi-page PDF documents and Plaintext. Layout preserved and embedded into 768-dim vectors.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center space-x-3 text-rose-300 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Documents Table Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">Your Grounded Knowledge Base</h3>
          <p className="text-xs text-slate-400">Indexed document inventory isolated by Supabase Row Level Security.</p>
        </div>
        <button
          onClick={fetchDocs}
          className="p-2 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition-all flex items-center space-x-1.5 text-xs font-medium"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
            <span className="text-sm">Querying document registry...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="py-16 text-center text-slate-400 space-y-2">
            <FileCode className="h-10 w-10 text-slate-600 mx-auto" />
            <p className="text-sm font-medium text-slate-300">No documents ingested yet.</p>
            <p className="text-xs text-slate-500">Upload a PDF above to ground your personal RAG assistant.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Document</th>
                  <th className="py-3.5 px-4">Pages</th>
                  <th className="py-3.5 px-4">Size</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-white flex items-center space-x-2.5">
                      <FileText className="h-4 w-4 text-teal-400 shrink-0" />
                      <span className="truncate max-w-xs">{doc.name}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{doc.page_count}</td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3.5 px-4">
                      {doc.status === 'completed' && (
                        <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Completed</span>
                        </span>
                      )}
                      {(doc.status === 'processing' || doc.status === 'pending') && (
                        <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>{doc.status === 'pending' ? 'Pending' : 'Ingesting...'}</span>
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <span
                          title={doc.error_message || 'Ingestion failed'}
                          className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 cursor-help"
                        >
                          <AlertCircle className="h-3 w-3" />
                          <span>Failed</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.name)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all"
                        title="Delete Document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

