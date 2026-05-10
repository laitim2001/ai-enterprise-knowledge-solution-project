'use client';

/**
 * KB Upload (`/kb/[id]/upload`) — per architecture.md v6 §5.5 KB Detail (rendered inside <AppShell>; route flattened W18 F3 per ADR-0024).
 *
 * W12 D4 F4.8 tokens migration: hardcoded oklch → token classes;
 * Upload CTA upgraded to shadcn Button. Functional logic intact (multipart
 * upload form to POST /kb/{id}/documents).
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { kbApi } from '@/lib/api/kb';

export default function KbUploadPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [file, setFile] = useState<File | null>(null);

  const mutation = useMutation({
    mutationFn: (f: File) => kbApi.uploadDoc(params.id, f),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb', params.id] });
      queryClient.invalidateQueries({ queryKey: ['kb', 'list'] });
      router.push(`/kb/${params.id}`);
    },
  });

  return (
    <div className="max-w-xl">
      <Link
        href={`/kb/${params.id}`}
        className="text-sm text-accent hover:underline"
      >
        ← Back to KB
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Upload Document</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Accepts .docx, .pdf, .pptx (per architecture.md §3.3).
      </p>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (file) mutation.mutate(file);
        }}
        className="mt-6 space-y-4"
      >
        <input
          type="file"
          accept=".docx,.pdf,.pptx"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm"
        />

        <Button type="submit" disabled={!file || mutation.isPending}>
          {mutation.isPending ? 'Uploading…' : 'Upload + Ingest'}
        </Button>

        {mutation.isError && (
          <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm">
            Upload failed: {String((mutation.error as Error)?.message)}
          </div>
        )}
      </form>
    </div>
  );
}
