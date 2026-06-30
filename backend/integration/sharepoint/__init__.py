"""SharePoint connector (C17 first concrete connector, per ADR-0070 + 方案藍圖 §4).

Maps the provider-agnostic `SourceConnector` (integration/connector.py) onto
SharePoint via Microsoft Graph, using managed-REST (azure-identity + httpx) —
no msgraph-sdk, zero new dependency (matches api/auth/entra_graph.py precedent,
blueprint §2.5 / §4.2).
"""
