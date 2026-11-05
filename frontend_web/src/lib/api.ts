import { DocumentItem, Message, Conversation, Citation } from '../types';

const isLocalhost = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const API_BASE = (import.meta.env.VITE_API_BASE_URL && import.meta.env.VITE_API_BASE_URL.trim() !== '')
  ? import.meta.env.VITE_API_BASE_URL.trim()
  : (isLocalhost ? 'https://rag-app-db2l.onrender.com' : '');

export async function listDocuments(token: string): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE}/api/documents`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to list documents: ${res.statusText}`);
  }
  return res.json();
}

export async function uploadDocument(file: File, token: string): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }

  return res.json();
}

export async function getDocumentStatus(id: string, token: string): Promise<{ id: string; status: string; page_count: number; error_message?: string }> {
  const res = await fetch(`${API_BASE}/api/documents/${id}/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Status check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteDocument(id: string, token: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/documents/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Delete failed: ${res.statusText}`);
  }
}

export async function listConversations(token: string): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE}/api/chat/conversations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to list conversations: ${res.statusText}`);
  }
  return res.json();
}

export async function getConversationMessages(conversationId: string, token: string): Promise<Message[]> {
  const res = await fetch(`${API_BASE}/api/chat/conversations/${conversationId}/messages`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch messages: ${res.statusText}`);
  }
  return res.json();
}

export async function sendChatMessageStream(
  token: string,
  params: { conversation_id?: string | null; message: string },
  onToken: (tokenText: string) => void,
  onDone: (payload: { answer: string; citations: Citation[]; conversation_id?: string }) => void,
  onError: (errorMsg: string) => void
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        conversation_id: params.conversation_id || null,
        message: params.message,
        stream: true,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      onError(err.detail || 'Chat query failed');
      return;
    }

    if (!res.body) {
      onError('Empty response stream from server');
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.replace('data: ', '').trim());
            if (data.token) {
              onToken(data.token);
            }
            if (data.done) {
              onDone({
                answer: data.answer || '',
                citations: data.citations || [],
                conversation_id: params.conversation_id || undefined,
              });
            }
          } catch {
            // Partial JSON chunk
          }
        }
      }
    }
  } catch (err: any) {
    onError(err.message || 'Stream connection error');
  }
}

