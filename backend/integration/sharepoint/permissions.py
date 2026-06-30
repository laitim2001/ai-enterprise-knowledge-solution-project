"""SharePoint ACL → `allowed_principals` mapping (§5) — the hardest integration step.

Collapse SharePoint's permission model (direct grants, sharing links, nested groups,
special principals) into a flat principal-id set EKP's query-time security filter
matches (the convergence point = `allowed_principals`, shared with the RBAC track).

Rules (方案藍圖 §5 + DG-INT-3 ①):
- nested groups expand to GROUP level via `transitiveMembers` (NOT user level) — zero
  re-ingest on membership change (§5.3), consistent with RBAC ADR-0067.
- Anyone (anonymous) links have no resolvable Entra principal → policy-driven:
  drop (default, D-2) / public / reject-the-document (§5.4).
- org-wide ("organization") links → a single tenant-wide org principal (§5.4).
- SharePoint local groups (siteGroup) → external_group (§5.4; best-effort 階段 1).
- 防爆量: cap the principal set per file (§5.5).
- An EMPTY result means "no resolvable principal", NOT public — the caller must
  refuse to index it as public (§6 risk; enforced in import_service, F5).
"""

from __future__ import annotations

from typing import Any, Literal

import structlog

from integration.models import Principal
from integration.sharepoint.graph_client import GraphClient

logger = structlog.get_logger(__name__)

AnyonePolicy = Literal["drop", "public", "reject"]

# §5.5 — single-user group membership becomes unpredictable past this; we cap the
# per-file principal set at the same bound.
MAX_PRINCIPALS_PER_FILE = 2049

# Sentinel principal for an org-wide ("organization") sharing link — a stable token
# representing "everyone in the tenant" (§5.4). Tenant-scoped so multi-tenant never
# collides.
def _org_principal_id(tenant_id: str) -> str:
    return f"org::{tenant_id}"


# Sentinel for an Anyone link under policy="public". NOTE: making this actually grant
# everyone requires the query side to inject it into every user's principal set — a
# follow-up; not exercised under the default drop policy (D-2).
PUBLIC_PRINCIPAL = "anyone::public"


class AclResolutionError(Exception):
    """The ACL could not be resolved (permission fetch failed, or policy=reject hit an
    Anyone link). The caller records a per-doc failure — it must NOT fail open to
    public (§6 risk)."""


def _identity_set_principals(idset: dict[str, Any]) -> list[Principal]:
    """An identitySet (user / group / siteGroup) → principals. Other identity kinds
    (application / device) are ignored — not access principals for our purposes."""
    out: list[Principal] = []
    user = idset.get("user")
    if isinstance(user, dict) and user.get("id"):
        out.append(Principal("user", user["id"], user.get("displayName") or ""))
    group = idset.get("group")
    if isinstance(group, dict) and group.get("id"):
        out.append(Principal("group", group["id"], group.get("displayName") or ""))
    site_group = idset.get("siteGroup")
    if isinstance(site_group, dict) and site_group.get("id"):
        # SharePoint local group — non-Entra GUID (§5.4) → external_group.
        out.append(
            Principal("external_group", site_group["id"], site_group.get("displayName") or "")
        )
    return out


async def _expand_group_to_group_level(
    graph: GraphClient,
    group_id: str,
    sink: dict[str, Principal],
    *,
    max_principals: int,
) -> bool:
    """Add nested GROUP members of `group_id` to `sink` (① — group level only, users
    skipped). Returns True if the cap was hit (caller stops)."""
    async for member in graph.paged(f"/groups/{group_id}/transitiveMembers"):
        otype = str(member.get("@odata.type", ""))
        if not otype.endswith("group"):
            continue  # ① skip user / device / contact members — group level only
        mid = member.get("id")
        if not mid:
            continue
        sink[mid] = Principal("group", mid, member.get("displayName") or "")
        if len(sink) >= max_principals:
            logger.warning(
                "acl_principal_cap_hit",
                group_id=group_id,
                cap=max_principals,
            )
            return True
    return False


async def resolve_principals(
    graph: GraphClient,
    drive_id: str,
    item_id: str,
    *,
    tenant_id: str,
    anyone_policy: AnyonePolicy = "drop",
    max_principals: int = MAX_PRINCIPALS_PER_FILE,
) -> list[Principal]:
    """Resolve a driveItem's `/permissions` into a deduped principal list (§5.2).

    Raises `AclResolutionError` if the permission fetch fails or an Anyone link is
    hit under policy=reject. An empty return is a valid "no resolvable principal"
    result — NOT public (§6; the caller refuses to index it as public).
    """
    sink: dict[str, Principal] = {}
    capped = False
    try:
        perms = [
            p
            async for p in graph.paged(f"/drives/{drive_id}/items/{item_id}/permissions")
        ]
    except Exception as exc:  # noqa: BLE001 — surface as a typed ACL failure (no fail-open)
        raise AclResolutionError(
            f"permission fetch failed for {drive_id}/{item_id}: {type(exc).__name__}"
        ) from exc

    for perm in perms:
        if capped:
            break
        link = perm.get("link")
        if isinstance(link, dict):
            scope = link.get("scope")
            if scope == "anonymous":  # Anyone link — no resolvable Entra principal
                if anyone_policy == "reject":
                    raise AclResolutionError(
                        f"anyone-link present on {drive_id}/{item_id}; policy=reject"
                    )
                if anyone_policy == "public":
                    sink[PUBLIC_PRINCIPAL] = Principal("org", PUBLIC_PRINCIPAL, "anyone")
                else:  # drop (default, D-2) — index nothing for this grant
                    logger.info("acl_anyone_link_dropped", item=f"{drive_id}/{item_id}")
                continue
            if scope == "organization":  # everyone in the tenant
                oid = _org_principal_id(tenant_id)
                sink[oid] = Principal("org", oid, "organization")
                # scope=organization carries no per-identity grants; fall through to
                # also pick up any grantedToIdentitiesV2 (defensive — usually empty).

        # Direct grant (grantedToV2) + link-shared identities (grantedToIdentitiesV2).
        idsets: list[dict[str, Any]] = []
        granted = perm.get("grantedToV2")
        if isinstance(granted, dict):
            idsets.append(granted)
        identities = perm.get("grantedToIdentitiesV2")
        if isinstance(identities, list):
            idsets.extend(i for i in identities if isinstance(i, dict))

        for idset in idsets:
            for principal in _identity_set_principals(idset):
                sink[principal.id] = principal
                if len(sink) >= max_principals:
                    logger.warning(
                        "acl_principal_cap_hit", item=f"{drive_id}/{item_id}", cap=max_principals
                    )
                    capped = True
                    break
                if principal.kind == "group":
                    capped = await _expand_group_to_group_level(
                        graph, principal.id, sink, max_principals=max_principals
                    )
            if capped:
                break

    return list(sink.values())
