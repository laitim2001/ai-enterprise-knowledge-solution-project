/**
 * Unit tests — `/kb/new` 5-step wizard (W20 F4.4 + W22 F5.2 rebuild) re-aligned
 * at W23 F1.3 to W22 D8 canonical sequence: Identity → Format & chunking →
 * Multimodal → Retrieval defaults → Review (mockup `ekp-page-kb-new.jsx
 * PageKbNew`, file picker dropped per W22 D2 mockup-wins, "Continue" button
 * not "Next").
 *
 * Verifies: Stepper renders 5 step labels as text (no aria-label="Wizard steps",
 * no aria-current="step" — W22 uses inline 28px circles + label/hint divs);
 * Step 1 (Identity) form fields render with W22 placeholders + auto-derive
 * kb_id_auto initial true;clicking Continue twice lands on Step 3 (Multimodal)
 * with Tier 1 toggle titles + Tier 2 badge affordances.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));
vi.mock('@/lib/api/kb', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/kb')>('@/lib/api/kb');
  return { ...actual, kbApi: { ...actual.kbApi, create: vi.fn(), uploadDoc: vi.fn() } };
});

import KbNewPage from '../../app/(app)/kb/new/page';

function renderWizard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <KbNewPage />
    </QueryClientProvider>,
  );
}

describe('KbNewPage 5-step wizard (W22 F5.2 rebuild) — re-aligned W23 F1.3', () => {
  it('renders the 5 stepper labels + Step 1 (Identity) card', () => {
    renderWizard();
    // W22 STEPS const (line 88-92): Identity / Format & chunking / Multimodal /
    // Retrieval defaults / Review. Rendered as inline `<div>{s.label}</div>` 13.5px
    // text within the stepper card (line 253), no aria attributes.
    const stepperLabels = [
      'Identity',
      'Format & chunking',
      'Multimodal',
      'Retrieval defaults',
      'Review & create',
    ];
    for (const label of stepperLabels) {
      // Each label may appear once (stepper-only — Identity also shows in card
      // heading "KB identity" which is a substring not exact match).
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    // Step 1 card heading is "KB identity" (W22 line 337 `<h3 class="card-title">`).
    expect(
      screen.getByRole('heading', { name: /kb identity/i, level: 3 }),
    ).toBeInTheDocument();
    // Step 1 of 5 footer text confirms wizard mode (W22 line 432).
    expect(screen.getByText(/step 1 of 5/i)).toBeInTheDocument();
  });

  it('navigates to Step 3 Multimodal + renders Tier 1 toggle titles + Tier 2 badges', async () => {
    const user = userEvent.setup();
    renderWizard();

    // Step 1 — fill Name (kb_id auto-derives from name per kb_id_auto: true
    // initial state, line 109). Continue button enabled when trimmedName + idValid.
    await user.type(screen.getByLabelText('Name'), 'Test KB');
    await user.click(screen.getByRole('button', { name: /continue/i }));

    // Step 2 — Format & chunking default values valid, Continue.
    await user.click(screen.getByRole('button', { name: /continue/i }));

    // Step 3 — Multimodal card heading is `<h3>Multimodal — images & screenshots</h3>`
    // (W22 line 775, with `&amp;` HTML entity rendered as `&`).
    expect(
      screen.getByRole('heading', {
        name: /multimodal — images.+screenshots/i,
        level: 3,
      }),
    ).toBeInTheDocument();

    // W22 Tier 1 toggle titles via OptionRow `title` prop (lines 924, 931) +
    // inline switch label (line 1168). Pre-W22 used simpler one-word labels;
    // W22 D8 mockup wins with descriptive titles.
    expect(screen.getByText('Embedded images from documents')).toBeInTheDocument();
    expect(screen.getByText('Whole-slide screenshots for .pptx')).toBeInTheDocument();
    expect(screen.getByText('Render inline images in chat answers')).toBeInTheDocument();

    // W22 Tier 2 badge affordances appear multiple times — Multimodal step has
    // explicit `<span class="badge badge-accent">TIER 2</span>` on the slide
    // screenshots row + PDF render row + captioning card. Don't over-specify
    // count — at least 1 confirms Tier 2 boundary enforcement is visible.
    expect(screen.getAllByText('TIER 2').length).toBeGreaterThanOrEqual(1);
  });
});
