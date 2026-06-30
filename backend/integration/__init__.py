"""C17 Source Abstraction Framework (per ADR-0070 + architecture.md §3.3/§4.1).

Provider-agnostic integration layer: a `SourceConnector` turns some external
source (SharePoint, …) into standardized documents + ACL principals + metadata,
which EKP's existing Docling ingestion core consumes unchanged (設計鐵律 §0.4 —
換來源 = 換 adapter, ingestion 核心零改動).

階段 1 (W100) ships the abstract layer + one concrete connector (SharePoint).
multi-provider + auto-sync are Tier 2 (階段 2/3, H4).
"""
