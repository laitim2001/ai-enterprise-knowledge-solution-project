'use client';

/**
 * Traces (`/traces`) — the Traces-module landing (W18 F3, per ADR-0024 + architecture.md v6 §5.0 sidebar).
 *
 * Tier 1 = a thin entry point: open a trace from a query result, or jump to one by trace ID.
 * The per-trace 9-stage inspector is /traces/[traceId] (V6, architecture.md §5.7 — formerly
 * "Debug View" /debug/[traceId]). A richer trace listing / search is a later-tier concern (the
 * backend exposes per-trace fetch `GET /debug/trace/{trace_id}`, not a trace list yet).
 */

import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function TracesPage() {
  const router = useRouter();
  const [traceId, setTraceId] = useState('');

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const id = traceId.trim();
    if (id) router.push(`/traces/${encodeURIComponent(id)}`);
  }

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Traces</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Inspect a query&apos;s pipeline trace (retrieval → rerank → CRAG → synthesis). Open one
          from a query result&apos;s &ldquo;inspect&rdquo; link, or enter a trace ID below.
        </p>
      </div>
      <form onSubmit={onSubmit} className="flex gap-2">
        <Input
          value={traceId}
          onChange={(e) => setTraceId(e.target.value)}
          placeholder="trace ID"
          aria-label="Trace ID"
          className="font-mono"
        />
        <Button type="submit" disabled={!traceId.trim()}>
          Open trace
        </Button>
      </form>
    </div>
  );
}
