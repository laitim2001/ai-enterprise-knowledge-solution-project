'use client';

/**
 * SharePoint import wizard — 4 steps (connect → select → import → done).
 *
 * Scaffold (F2): real H7 reproduction of `references/design-mockups/
 * integration-import/20..23-*.html` lands in F5 (step 1 Connect + step 2 Select)
 * and F6 (step 3 Import + step 4 Summary). Inline stepper + useState step state
 * per existing wizard pattern (kb/new, kb/[id]/upload), D-2 (no shared Stepper).
 */
export default function SharePointImportPage() {
  return (
    <div className="content">
      <div className="content-narrow">
        <div className="page-header">
          <div>
            <h1 className="page-title">Import from SharePoint</h1>
            <p className="page-subtitle">
              Connect a site, pick documents, and import them through the EKP
              ingestion pipeline.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
