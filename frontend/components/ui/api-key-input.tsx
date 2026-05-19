'use client';

/**
 * `<ApiKeyInput>` primitive (W24-wave-c1 F5 per ADR-0026 + mockup line 725-741).
 *
 * Renders a masked-by-default monospace input with 3 inline actions:
 *  - **Reveal/Hide** — flips `type` between `password` and `text`
 *  - **Copy** — copies the visible value to clipboard via `navigator.clipboard`
 *  - **Rotate** — fires `onRotate` mutation (backend POST /admin/connections/{id}/rotate-secret)
 *
 * **Security hygiene per ADR-0026 §Consequences**:
 *  - The "value" shown is **never** the real secret. It's the masked preview
 *    (e.g. `***xY1z`) emitted by the backend. Reveal toggles the input `type`
 *    but the underlying value is still the masked preview.
 *  - Real secret only exists in Key Vault server-side. Rotate mints a new
 *    value via Azure SDK; UI receives only the new masked preview.
 *
 * Wave C1 ships read-mostly — the input is `readOnly` since `client_secret`
 * fields are managed via rotate, not direct edit.
 */

import { Copy, Eye, EyeOff, RefreshCw } from 'lucide-react';
import { useState } from 'react';

interface ApiKeyInputProps {
  /** Masked preview from backend (e.g. `***xY1z` or `<not provisioned>`). */
  value: string | null | undefined;
  /** Triggered by the Rotate button. Disable button while pending. */
  onRotate?: () => void | Promise<void>;
  /** Disable Rotate (e.g. when secret_kv_ref is null = managed-identity provider). */
  rotateDisabled?: boolean;
  /** Tooltip shown over Rotate when disabled. */
  rotateDisabledReason?: string;
  /** Aria label override (defaults to "API secret value"). */
  ariaLabel?: string;
}

export function ApiKeyInput({
  value,
  onRotate,
  rotateDisabled = false,
  rotateDisabledReason,
  ariaLabel = 'API secret value',
}: ApiKeyInputProps) {
  const [reveal, setReveal] = useState(false);
  const [rotating, setRotating] = useState(false);
  const displayValue = value ?? '<not provisioned>';

  const handleCopy = () => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      void navigator.clipboard.writeText(displayValue);
    }
  };

  const handleRotate = async () => {
    if (!onRotate || rotateDisabled || rotating) return;
    setRotating(true);
    try {
      await onRotate();
    } finally {
      setRotating(false);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'flex' }}>
      <input
        className="input mono"
        value={displayValue}
        readOnly
        type={reveal ? 'text' : 'password'}
        aria-label={ariaLabel}
        style={{ fontSize: 12, paddingRight: 80 }}
      />
      <div
        style={{
          position: 'absolute',
          right: 4,
          top: 4,
          display: 'flex',
          gap: 2,
        }}
      >
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-xs"
          onClick={() => setReveal(!reveal)}
          title={reveal ? 'Hide' : 'Reveal'}
          aria-label={reveal ? 'Hide secret' : 'Reveal secret'}
        >
          {reveal ? (
            <EyeOff size={11} aria-hidden="true" />
          ) : (
            <Eye size={11} aria-hidden="true" />
          )}
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-xs"
          onClick={handleCopy}
          title="Copy"
          aria-label="Copy secret preview to clipboard"
        >
          <Copy size={11} aria-hidden="true" />
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-xs"
          onClick={() => void handleRotate()}
          disabled={rotateDisabled || rotating || !onRotate}
          title={rotateDisabled ? rotateDisabledReason ?? 'Rotate disabled' : 'Rotate secret'}
          aria-label="Rotate secret"
        >
          <RefreshCw size={11} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
