export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DocumentItem {
  id: string;
  name: string;
  storage_path: string;
  file_size: number;
  mime_type: string;
  page_count: number;
  status: DocumentStatus;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id?: string | null;
  document_name: string;
  page_number: number;
  passage_preview?: string | null;
  similarity?: number | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  is_approved: boolean;
}

