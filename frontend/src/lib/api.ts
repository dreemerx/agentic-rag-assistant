const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const endpoints = {
  chat: `${API_BASE}/api/v1/chat/stream`,
  completions: `${API_BASE}/api/v1/chat/completions`,
  providers: `${API_BASE}/api/v1/chat/providers`,
  ragUpload: `${API_BASE}/api/v1/rag/upload`,
  ragQuery: `${API_BASE}/api/v1/rag/query`,
  ragFiles: `${API_BASE}/api/v1/rag/files`,
  agentChat: `${API_BASE}/api/v1/agent/chat`,
  agentReset: `${API_BASE}/api/v1/agent/reset`,
  wsChat: `${WS_BASE}/ws/chat`,
};

export async function fetchProviders(): Promise<{
  providers: string[];
  default: string;
}> {
  const res = await fetch(endpoints.providers);
  return res.json();
}
