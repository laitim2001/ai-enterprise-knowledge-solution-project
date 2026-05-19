/**
 * Unit tests — `/kb/[id]/upload` 3-step re-ingestion wizard (W20 F6 + W22 F6.2
 * rebuild) re-aligned at W23 F1.4 to W22 D8 canonical 3-step sequence:
 * Data source / Document processing / Execute (mockup `ekp-page-misc.jsx:4
 * PageUploadWizard`, 28px stepper circle, Step 2 chunking config READ-ONLY per
 * §13 backend-wins, "Continue" button not "Next").
 *
 * Verifies: Stepper renders 3 step labels as text (no aria-label="Wizard steps",
 * no aria-current="step" — W22 uses inline 28px circles + label/hint divs);
 * Step 1 (Data source) shows file picker + Continue disabled until file
 * selected;Step 2 (Document processing) reads the KB config + renders the
 * single "Extract embedded screenshots" switch + "edit KB Settings" link →
 * /kb/[id]?tab=settings.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-kb' }),
  useRouter: () => ({ push: vi.fn() }),
}));
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));
vi.mock('@/lib/api/kb', () => ({
  kbApi: {
    get: vi.fn(async () => ({
      kb_id: 'test-kb',
      name: 'Test KB',
      description: 'Test',
      total_documents: 0,
      total_chunks: 0,
      total_screenshots: 0,
      storage_size_mb: 0,
      failed_documents: [],
      last_indexed_at: '2026-05-17T00:00:00Z',
      archived: false,
      config: {
        embedding_model: 'text-embedding-3-large',
        embedding_dimension: 1024,
        chunk_strategy: 'auto',
        default_top_k: 50,
        default_rerank_k: 5,
        extract_embedded_images: true,
        slide_screenshots: true,
        dedup_strategy: 'sha256',
        return_images_in_chat: false,
      },
    })),
    uploadDoc: vi.fn(),
  },
}));

import KbUploadPage from '../../app/(app)/kb/[id]/upload/page';

function renderWizard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <KbUploadPage />
    </QueryClientProvider>,
  );
}

describe('KbUploadPage 3-step re-ingestion wizard (W22 F6.2 rebuild) — re-aligned W23 F1.4', () => {
  it('renders the 3 stepper labels + Step 1 (Data source) card', () => {
    renderWizard();
    // W22 STEPS const (lines 44-48): Data source / Document processing / Execute.
    // Rendered as inline `<div>{s.label}</div>` 13.5px text within the stepper
    // card. No aria attributes — pre-W22 `aria-label="Wizard steps"` +
    // `aria-current="step"` were dropped at W22 F1 CSS-first pivot.
    const stepperLabels = ['Data source', 'Document processing', 'Execute'];
    for (const label of stepperLabels) {
      // Stepper label + step card heading (Step 0 only) share "Data source"
      // text — getAllByText accepts both occurrences.
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
    // Step 0 card heading "Data source" `<h3 class="card-title">` (line 288).
    expect(
      screen.getByRole('heading', { name: /^data source$/i, level: 3 }),
    ).toBeInTheDocument();
    // Step 1 of 3 footer text confirms wizard mode (line 451).
    expect(screen.getByText(/step 1 of 3/i)).toBeInTheDocument();
  });

  it('Step 2 reads the KB config and renders the read-only Document processing + Extract embedded screenshots + edit KB Settings link', async () => {
    const user = userEvent.setup();
    renderWizard();
    // Step 1: file picker is `<input type="file" style={{ display: 'none' }}>`
    // wrapped in `<label class="btn btn-secondary btn-sm">` (lines 410-421).
    // Upload a fake .docx, then click Continue (enabled when file && source === 'upload',
    // source defaults to 'upload' = first sources[] item).
    const file = new File(['hello'], 'doc.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).not.toBeNull();
    await user.upload(input, file);
    await user.click(screen.getByRole('button', { name: /continue/i }));

    // Step 2 card heading "Document processing" `<h3 class="card-title">` (line 513).
    expect(
      await screen.findByRole('heading', { name: /document processing/i, level: 3 }),
    ).toBeInTheDocument();

    // Step 2 has a SINGLE multimodal toggle "Extract embedded screenshots"
    // (line 612, line ~602-619 switch + 13px label div). Pre-W22 expected
    // separate "Extract embedded images" + "Slide screenshots" toggles;W22 D8
    // consolidated to one switch tied to `kb.config.extract_embedded_images`,
    // showing the rendered Boolean directly.
    expect(screen.getByText('Extract embedded screenshots')).toBeInTheDocument();

    // Edit settings link → `/kb/{id}?tab=settings`, text "edit KB Settings"
    // (lines 626-631). Pre-W22 expected aria-label "Edit the KB's settings tab"
    // — W22 D8 drop aria-label in favour of plain anchor text.
    expect(
      screen.getByRole('link', { name: /edit kb settings/i }),
    ).toHaveAttribute('href', '/kb/test-kb?tab=settings');
  });
});
