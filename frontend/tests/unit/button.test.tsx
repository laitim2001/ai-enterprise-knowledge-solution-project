/**
 * Sample unit test — `@/components/ui/button` (W17 F6 harness proof).
 *
 * Covers: (1) renders children + the default token-class variant
 * (`bg-primary text-primary-foreground` — the design-token consumption path
 * via cva), (2) the `destructive` variant swaps to `bg-destructive`, (3) an
 * `onClick` handler fires on a `user-event` click. This is a render/interaction
 * smoke — deep component coverage is Tier 2 (see README.md).
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('renders children and the default token-class variant', () => {
    render(<Button>Save settings</Button>);
    const btn = screen.getByRole('button', { name: 'Save settings' });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveClass('bg-primary');
    expect(btn).toHaveClass('text-primary-foreground');
  });

  it('applies the destructive variant', () => {
    render(<Button variant="destructive">Delete KB</Button>);
    const btn = screen.getByRole('button', { name: 'Delete KB' });
    expect(btn).toHaveClass('bg-destructive');
    expect(btn).not.toHaveClass('bg-primary');
  });

  it('fires onClick on a user click', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Run end-to-end</Button>);
    await userEvent.click(screen.getByRole('button', { name: 'Run end-to-end' }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
