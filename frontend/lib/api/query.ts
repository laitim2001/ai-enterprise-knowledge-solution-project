/**
 * Query API — types + SSE stream consumer (per architecture.md §4.5 + §5.2).
 *
 * Backend `/query/stream` emits Vercel AI SDK-style SSE frames (W3 D3 F4):
 *   data: {"type":"text-delta","content":str}\n\n
 *   data: {"type":"citation","citation":{...}}\n\n
 *   data: {"type":"done","model","latency_ms","refused","reranker_used"}\n\n
 *
 * `streamQuery` is an async generator yielding parsed `SseEvent` objects so
 * the chat page can drive React state per-event. We use native fetch streaming
 * rather than Vercel AI SDK `useChat` because our event protocol is JSON-encoded
 * (custom citation + done events) — wrapping `useChat` would add an indirection
 * for no benefit (per Karpathy §1.2 simplicity).
 */
import { ApiError } from '../api-client';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export interface ImageRef {
  blob_url: string;
  alt_text: string;
  checksum_sha256: string;
  width: number;
  height: number;
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  doc_title: string;
  chunk_title: string;
  chunk_index: number;
  section_path: string[];
  relevance_score: number;
  embedded_images: ImageRef[];
}

export interface QueryRequest {
  query: string;
  kb_id: string;
  top_k_retrieval?: number;
  top_k_rerank?: number;
  llm_model?: 'gpt-5.5' | 'gpt-5.4-mini';
  reranker?:
    | 'cohere-v3.5'
    | 'voyage-rerank-2.5'
    | 'zeroentropy-zerank-1'
    | 'azure-semantic'
    | 'off';
  enable_crag?: boolean;
  enable_intent_routing?: boolean;
}

export interface TextDeltaEvent {
  type: 'text-delta';
  content: string;
}

export interface CitationEvent {
  type: 'citation';
  citation: Citation;
}

export interface DoneEvent {
  type: 'done';
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  refused: boolean;
  reranker_used: string;
}

export type SseEvent = TextDeltaEvent | CitationEvent | DoneEvent;

/**
 * Stream events from `/query/stream`. Aborts when caller breaks the loop OR
 * passes an `AbortSignal` that fires.
 */
export async function* streamQuery(
  payload: QueryRequest,
  signal?: AbortSignal,
): AsyncGenerator<SseEvent> {
  const response = await fetch(`${API_URL}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok || !response.body) {
    const errBody = response.body ? await response.text() : '(no body)';
    throw new ApiError(response.status, errBody);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames separated by `\n\n`
      let sepIdx: number;
      while ((sepIdx = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, sepIdx);
        buffer = buffer.slice(sepIdx + 2);
        if (!frame.startsWith('data: ')) continue;
        const json = frame.slice(6).trim();
        if (!json) continue;
        try {
          yield JSON.parse(json) as SseEvent;
        } catch {
          // Malformed frame — skip silently; backend should never emit this
          continue;
        }
      }
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {
      // ignore — already released or stream errored
    }
  }
}
