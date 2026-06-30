'use client';

/**
 * Integrations landing — top-level source-integration module (ADR-0071).
 *
 * Scaffold (F2): real H7 reproduction of `references/design-mockups/
 * integration-import/10-integrations-landing.html` (SharePoint connector card +
 * disabled "connect another source" affordance) lands in F4.
 */
export default function IntegrationsPage() {
  return (
    <div className="content">
      <div className="content-narrow">
        <div className="page-header">
          <div>
            <h1 className="page-title">Integrations</h1>
            <p className="page-subtitle">
              Connect external content sources and import their documents into your
              knowledge bases.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
