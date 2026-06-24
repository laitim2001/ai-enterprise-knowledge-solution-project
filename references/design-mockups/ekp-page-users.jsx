// ekp-page-users.jsx — /users (user management) + roles & permissions matrix
// Per C11 Identity (Beta+) + C09 Tier 2 role-based view gating spec.
// Tier 1: 3 roles (Admin / Editor / End User) · Tier 2 adds Power User.

const MOCK_USERS = [
  { id: "u_001", name: "Chris Lai",      email: "chris.lai@ricoh.com",        role: "admin",   status: "active",  last_login: "2026-05-15T08:42:00Z", joined: "2026-04-01", source: "Entra ID SSO", group: "grp-ekp-admins",  queries_7d: 142, kbs_owned: 3, avatar: "CL" },
  { id: "u_002", name: "Priya Anand",    email: "priya.anand@ricoh.com",      role: "editor",  status: "active",  last_login: "2026-05-15T07:18:00Z", joined: "2026-04-08", source: "Entra ID SSO", group: "grp-ekp-editors", queries_7d: 84,  kbs_owned: 1, avatar: "PA" },
  { id: "u_003", name: "Daniel Kim",     email: "daniel.kim@ricoh.com",       role: "editor",  status: "active",  last_login: "2026-05-14T16:12:00Z", joined: "2026-04-10", source: "Entra ID SSO", group: "grp-ekp-editors", queries_7d: 56,  kbs_owned: 1, avatar: "DK" },
  { id: "u_004", name: "Mei-Ling Wu",    email: "mei.wu@ricoh.co.jp",         role: "editor",  status: "active",  last_login: "2026-05-15T03:30:00Z", joined: "2026-04-15", source: "Entra ID SSO", group: "grp-ekp-editors", queries_7d: 38,  kbs_owned: 1, avatar: "MW" },
  { id: "u_005", name: "Yuki Tanaka",    email: "yuki.tanaka@ricoh.co.jp",    role: "user",    status: "active",  last_login: "2026-05-15T01:20:00Z", joined: "2026-04-20", source: "Entra ID SSO", group: "grp-ekp-users",   queries_7d: 24,  kbs_owned: 0, avatar: "YT" },
  { id: "u_006", name: "Carlos Ramirez", email: "carlos.r@ricoh.com",         role: "user",    status: "active",  last_login: "2026-05-14T22:08:00Z", joined: "2026-04-22", source: "Self-register", group: "grp-ekp-users",  queries_7d: 18,  kbs_owned: 0, avatar: "CR" },
  { id: "u_007", name: "Aisha Patel",    email: "aisha.patel@ricoh.com",      role: "user",    status: "active",  last_login: "2026-05-14T18:42:00Z", joined: "2026-05-02", source: "Entra ID SSO", group: "grp-ekp-users",   queries_7d: 12,  kbs_owned: 0, avatar: "AP" },
  { id: "u_008", name: "Marco Silva",    email: "marco.silva@ricoh.com",      role: "user",    status: "active",  last_login: "2026-05-13T11:30:00Z", joined: "2026-05-04", source: "Self-register", group: "grp-ekp-users",  queries_7d: 8,   kbs_owned: 0, avatar: "MS" },
  { id: "u_009", name: "Hana Suzuki",    email: "hana.suzuki@ricoh.co.jp",    role: "user",    status: "pending", last_login: null,                    joined: "2026-05-14", source: "Self-register", group: "—",              queries_7d: 0,   kbs_owned: 0, avatar: "HS" },
  { id: "u_010", name: "James O'Brien",  email: "james.obrien@ricoh.com",     role: "user",    status: "suspended", last_login: "2026-05-08T14:00:00Z", joined: "2026-04-25", source: "Entra ID SSO", group: "—",             queries_7d: 0,   kbs_owned: 0, avatar: "JO" },
  { id: "u_011", name: "Lisa Brown",     email: "lisa.brown@ricoh.com",       role: "user",    status: "invited", last_login: null,                    joined: "2026-05-15", source: "Email invite",  group: "—",              queries_7d: 0,   kbs_owned: 0, avatar: "LB" },
];

const ROLES = {
  admin:    { label: "Workspace Admin",   color: "oklch(var(--accent))",     desc: "Full platform control · manages KBs, users, providers, API keys" },
  editor:   { label: "Knowledge Editor",  color: "oklch(0.55 0.13 240)",     desc: "Create + upload to assigned KBs · manages own content · cannot change platform config" },
  user:     { label: "End User",          color: "oklch(0.55 0.16 145)",     desc: "Query assigned KBs · view own traces · no admin access" },
  power:    { label: "Power User",        color: "oklch(0.55 0.16 285)",     desc: "Tier 2 — End User + retrieval tuning + model picker access" },
};

const PERMISSIONS_MATRIX = [
  { area: "Knowledge bases",  perms: [
    { p: "View assigned KBs",       a: 1, e: 1, u: 1, w: 1 },
    { p: "Create new KB",           a: 1, e: 1, u: 0, w: 0 },
    { p: "Edit KB config",          a: 1, e: 1, u: 0, w: 0 },
    { p: "Trigger re-index",        a: 1, e: 1, u: 0, w: 0 },
    { p: "Delete KB",               a: 1, e: 0, u: 0, w: 0 },
    { p: "Manage KB access list",   a: 1, e: 0, u: 0, w: 0 },
  ]},
  { area: "Documents",  perms: [
    { p: "Upload to assigned KBs",  a: 1, e: 1, u: 0, w: 0 },
    { p: "Delete documents",        a: 1, e: 1, u: 0, w: 0 },
    { p: "View parse errors",       a: 1, e: 1, u: 0, w: 0 },
  ]},
  { area: "Chat & queries",  perms: [
    { p: "Query assigned KBs",      a: 1, e: 1, u: 1, w: 1 },
    { p: "View own traces",         a: 1, e: 1, u: 1, w: 1 },
    { p: "View all users' traces",  a: 1, e: 0, u: 0, w: 0 },
    { p: "Submit feedback",         a: 1, e: 1, u: 1, w: 1 },
    { p: "Tune top-K / rerank-K",   a: 1, e: 1, u: 0, w: 1 },
    { p: "Pick LLM model per query",a: 1, e: 0, u: 0, w: 1 },
  ]},
  { area: "Eval & ops",  perms: [
    { p: "View Eval Console",       a: 1, e: 1, u: 0, w: 1 },
    { p: "Run eval suite",          a: 1, e: 0, u: 0, w: 0 },
    { p: "View cost dashboard",     a: 1, e: 0, u: 0, w: 0 },
  ]},
  { area: "Platform config",  perms: [
    { p: "Manage LLM providers",    a: 1, e: 0, u: 0, w: 0 },
    { p: "Manage API keys",          a: 1, e: 0, u: 0, w: 0 },
    { p: "Manage Entra/Auth",        a: 1, e: 0, u: 0, w: 0 },
    { p: "Manage users + roles",     a: 1, e: 0, u: 0, w: 0 },
    { p: "View audit log",           a: 1, e: 0, u: 0, w: 0 },
  ]},
];

function PageUsers({ onNavigate, tweaks }) {
  const [tab, setTab] = useState("members");
  const [filter, setFilter] = useState("all");
  const [inviteOpen, setInviteOpen] = useState(false); // F4 — invite member modal
  const counts = {
    all: MOCK_USERS.length,
    admin:  MOCK_USERS.filter((u) => u.role === "admin").length,
    editor: MOCK_USERS.filter((u) => u.role === "editor").length,
    user:   MOCK_USERS.filter((u) => u.role === "user").length,
    pending: MOCK_USERS.filter((u) => u.status === "pending" || u.status === "invited").length,
  };
  const filtered = filter === "all"
    ? MOCK_USERS
    : filter === "pending"
      ? MOCK_USERS.filter((u) => u.status === "pending" || u.status === "invited")
      : MOCK_USERS.filter((u) => u.role === filter);

  return (
    <div className="content">
      <div className="content-wide">
        <div className="page-header">
          <div>
            <h1 className="page-title">Users & access</h1>
            <p className="page-subtitle">Workspace members · role assignment · per-KB access. Roles are mapped via Entra ID groups; assignments here update both Postgres <span className="mono">users</span> table and Entra group membership.</p>
          </div>
          <div className="page-actions">
            <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> Export CSV</button>
            <button className="btn btn-primary btn-sm" onClick={() => setInviteOpen(true)}><IcPlus size={13} /> Invite member</button>
          </div>
        </div>

        <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 16 }}>
          <Stat label="Total members" value={MOCK_USERS.length} sub={`${counts.admin} Admin · ${counts.editor} Editor · ${counts.user} User`} />
          <Stat label="Active sessions" value="6" sub="Last 24h · 5 SSO · 1 self-register" />
          <Stat label="Pending invites" value={counts.pending} sub="Email verification pending" />
          <Stat label="Avg queries / user" value="32" sub="Last 7d · ↑ 12% vs prev" />
        </div>

        <div className="tabs">
          <div className="tab" data-active={tab === "members"} onClick={() => setTab("members")}><IcUsers size={14} /> Members <span className="count">{MOCK_USERS.length}</span></div>
          <div className="tab" data-active={tab === "roles"} onClick={() => setTab("roles")}><IcShield size={14} /> Roles & permissions</div>
          <div className="tab" data-active={tab === "groups"} onClick={() => setTab("groups")}><IcLayers size={14} /> Groups</div>
          <div className="tab" data-active={tab === "audit"} onClick={() => setTab("audit")}><IcActivity size={14} /> Audit log</div>
        </div>

        {tab === "members" && <UsersTab filter={filter} setFilter={setFilter} counts={counts} filtered={filtered} onNavigate={onNavigate} />}
        {tab === "roles"   && <RolesTab />}
        {tab === "groups"  && <GroupsTab />}
        {tab === "audit"   && <AuditTab />}
      </div>
      {/* F4 — invite member modal (per DESIGN_SYSTEM §4.5) */}
      {inviteOpen && <InviteModal onClose={() => setInviteOpen(false)} />}
    </div>
  );
}

function UsersTab({ filter, setFilter, counts, filtered, onNavigate }) {
  // F4 — which row's ⋯ menu is open + the suspend-confirm target (null = none)
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [suspendUser, setSuspendUser] = useState(null);
  return (
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <div className="input-search-wrap" style={{ maxWidth: 320, flex: 1 }}>
          <span className="icon-leading"><IcSearch size={14} /></span>
          <input className="input" placeholder="Search by name, email, group…" />
        </div>
        <div className="seg">
          {[
            { id: "all",      label: "All" },
            { id: "admin",    label: "Admin" },
            { id: "editor",   label: "Editor" },
            { id: "user",     label: "User" },
            { id: "pending",  label: "Pending" },
          ].map((f) => (
            <button key={f.id} className="seg-btn" data-active={filter === f.id} onClick={() => setFilter(f.id)}>
              {f.label} <span className="text-xs mono" style={{ opacity: 0.6 }}>{counts[f.id]}</span>
            </button>
          ))}
        </div>
        <div className="spacer" />
        <button className="btn btn-secondary btn-sm"><IcFilter size={13} /> More filters</button>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: 26 }}><span className="kbd" style={{ padding: "0 4px" }}>☐</span></th>
              <th>Member</th>
              <th>Role</th>
              <th>Auth source</th>
              <th>Entra group</th>
              <th className="col-num">Queries (7d)</th>
              <th className="col-num">KBs owned</th>
              <th className="col-num">Last login</th>
              <th>Status</th>
              <th className="col-shrink"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id}>
                <td onClick={(e) => e.stopPropagation()}><span className="kbd" style={{ padding: "0 4px" }}>☐</span></td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div className="avatar avatar-sm">{u.avatar}</div>
                    <div>
                      <div className="table-row-link">{u.name}</div>
                      <div className="text-xs muted mono">{u.email}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <RoleBadge role={u.role} />
                </td>
                <td><span className="text-xs">{u.source}</span></td>
                <td className="col-mono">{u.group}</td>
                <td className="col-num">{u.queries_7d}</td>
                <td className="col-num">{u.kbs_owned}</td>
                <td className="col-num text-xs">{u.last_login ? window.formatRelative(u.last_login) : <span className="muted">—</span>}</td>
                <td>
                  {u.status === "active"    && <span className="badge badge-success"><span className="badge-dot" /> ACTIVE</span>}
                  {u.status === "pending"   && <span className="badge badge-warning"><span className="badge-dot" /> PENDING EMAIL</span>}
                  {u.status === "invited"   && <span className="badge badge-info"><span className="badge-dot" /> INVITED</span>}
                  {u.status === "suspended" && <span className="badge badge-error"><span className="badge-dot" /> SUSPENDED</span>}
                </td>
                <td className="col-shrink" style={{ position: "relative" }}>
                  <button
                    className="btn btn-ghost btn-icon btn-xs"
                    onClick={() => setMenuOpenId(menuOpenId === u.id ? null : u.id)}
                  >
                    <IcMore size={13} />
                  </button>
                  {/* F4 — row action menu: inline role change + suspend */}
                  {menuOpenId === u.id && (
                    <RowActionMenu
                      user={u}
                      onClose={() => setMenuOpenId(null)}
                      onSuspend={() => { setMenuOpenId(null); setSuspendUser(u); }}
                    />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* F4 — suspend confirm modal (per DESIGN_SYSTEM §4.5, destructive per §5) */}
      {suspendUser && <SuspendModal user={suspendUser} onClose={() => setSuspendUser(null)} />}
    </div>
  );
}

// F4 — invite member modal (DESIGN_SYSTEM §4.5). Presentational: shows the form
// shape the real /users page wires to POST /users/invite (email + role +
// display_name). Power User is Tier 2 → disabled option (DisabledAffordance §4.4).
function InviteModal({ onClose }) {
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">Invite member</h2>
          <p className="modal-desc">Pre-authorise an email + workspace role. An invite record is created (status = invited) and a verification email is sent.</p>
        </div>
        <div className="modal-body">
          <div className="field">
            <label className="label">Email address <span style={{ color: "oklch(var(--destructive))" }}>*</span></label>
            <input className="input" type="email" placeholder="name@ricoh.com" />
          </div>
          <div className="field">
            <label className="label">Display name</label>
            <input className="input" placeholder="Optional — derived from email if left blank" />
          </div>
          <div className="field">
            <label className="label">Workspace role</label>
            <select className="select" defaultValue="user">
              <option value="admin">Workspace Admin</option>
              <option value="editor">Knowledge Editor</option>
              <option value="user">End User</option>
              <option value="power" disabled>Power User · Tier 2</option>
            </select>
            <div className="hint">Power User is a Tier 2 role — not assignable in Tier 1.</div>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary btn-sm" onClick={onClose}><IcPlus size={13} /> Send invite</button>
        </div>
      </div>
    </div>
  );
}

// F4 — row action menu: row-anchored dropdown (NOT the topbar PopMenu §4.1 —
// that one is viewport-anchored). CHANGE ROLE lists the three Tier 1 roles
// inline (current marked ✓) → PATCH /users/{oid}/role; Suspend (destructive)
// opens the confirm modal. Reactivate / resend-invite have no backend endpoint
// yet → out of P0 scope.
function RowActionMenu({ user, onClose, onSuspend }) {
  const TIER1_ROLES = ["admin", "editor", "user"];
  const itemStyle = {
    display: "flex", alignItems: "center", gap: 8, width: "100%",
    padding: "7px 12px", fontSize: 12.5, textAlign: "left",
    background: "transparent", border: 0, cursor: "pointer",
  };
  return (
    <div style={{
      position: "absolute", right: 8, top: "100%", marginTop: 4, width: 210,
      background: "oklch(var(--popover))", border: "1px solid oklch(var(--border))",
      borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-lg)",
      zIndex: 30, overflow: "hidden", animation: "pop-in 0.14s var(--ease)",
    }}>
      <div style={{ padding: "8px 12px 4px", fontSize: 10.5, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase", color: "oklch(var(--muted-foreground))" }}>Change role</div>
      {TIER1_ROLES.map((rk) => (
        <button key={rk} style={{ ...itemStyle, color: "oklch(var(--foreground))" }} onClick={onClose}>
          <span style={{ width: 14, display: "inline-flex", flexShrink: 0 }}>
            {user.role === rk && <IcCheck size={12} style={{ color: "oklch(var(--accent))" }} />}
          </span>
          {ROLES[rk].label}
        </button>
      ))}
      <div style={{ height: 1, background: "oklch(var(--border))", margin: "4px 0" }} />
      <button style={{ ...itemStyle, color: "oklch(var(--destructive))" }} onClick={onSuspend}>
        <span style={{ width: 14, display: "inline-flex", flexShrink: 0 }}><IcShield size={12} /></span>
        Suspend member
      </button>
    </div>
  );
}

// F4 — suspend confirm modal (DESIGN_SYSTEM §4.5, destructive per §5).
// POST /users/{oid}/suspend (no body).
function SuspendModal({ user, onClose }) {
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">Suspend member?</h2>
          <p className="modal-desc"><b>{user.name}</b> ({user.email}) will lose access to all KBs and can no longer sign in. Re-invite to restore access.</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Cancel</button>
          <button className="btn btn-sm" style={{ background: "oklch(var(--destructive))", color: "#fff" }} onClick={onClose}>Suspend member</button>
        </div>
      </div>
    </div>
  );
}

function RoleBadge({ role }) {
  const r = ROLES[role];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "1px 7px",
      borderRadius: "var(--radius-sm)",
      fontSize: 11.5, fontWeight: 500,
      background: `${r.color.replace(")", " / 0.12)").replace("oklch(", "oklch(")}`,
      color: r.color,
      border: `1px solid ${r.color.replace(")", " / 0.3)")}`,
      fontFamily: "var(--font-mono)",
    }}>{r.label}</span>
  );
}

function RolesTab() {
  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="banner banner-info">
        <IcShield size={14} style={{ color: "oklch(var(--info))" }} />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>Role-based access control (RBAC)</div>
          <div className="text-xs muted">
            Tier 1: Admin / Editor / End User — view-gating enforced server-side per audit log. Tier 2: Power User adds advanced retrieval tuning. Permissions are not editable per ADR-0024 (predefined roles); custom roles are Tier 2.
          </div>
        </div>
      </div>

      {/* Role cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
        {Object.entries(ROLES).map(([key, r]) => {
          const count = MOCK_USERS.filter((u) => u.role === key).length;
          const isTier2 = key === "power";
          return (
            <div key={key} className="card" style={{ opacity: isTier2 ? 0.6 : 1 }}>
              <div className="card-body">
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <RoleBadge role={key} />
                  {isTier2 && <span className="badge badge-muted">TIER 2</span>}
                  <div className="spacer" />
                  <span className="mono text-xs muted">{count} member{count !== 1 ? "s" : ""}</span>
                </div>
                <div className="text-sm" style={{ lineHeight: 1.55 }}>{r.desc}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Permissions matrix */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Permissions matrix</h3>
            <div className="card-desc">What each role can do · ✓ = allowed · — = denied</div>
          </div>
          <button className="btn btn-ghost btn-sm"><IcDownload size={13} /> Export</button>
        </div>
        <div className="card-body card-body-tight">
          <table className="table" style={{ tableLayout: "fixed" }}>
            <thead>
              <tr>
                <th style={{ width: "44%" }}>Permission</th>
                <th style={{ textAlign: "center" }}>Admin</th>
                <th style={{ textAlign: "center" }}>Editor</th>
                <th style={{ textAlign: "center" }}>User</th>
                <th style={{ textAlign: "center", opacity: 0.6 }}>Power <span className="badge badge-muted" style={{ fontSize: 9 }}>T2</span></th>
              </tr>
            </thead>
            <tbody>
              {PERMISSIONS_MATRIX.map((g) => (
                <React.Fragment key={g.area}>
                  <tr style={{ background: "oklch(var(--muted) / 0.3)" }}>
                    <td colSpan={5} className="text-xs muted mono" style={{ padding: "8px 16px", letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 700 }}>{g.area}</td>
                  </tr>
                  {g.perms.map((p) => (
                    <tr key={p.p}>
                      <td>{p.p}</td>
                      <td style={{ textAlign: "center" }}>{p.a ? <IcCheck size={13} style={{ color: "oklch(var(--success))" }} /> : <span className="muted">—</span>}</td>
                      <td style={{ textAlign: "center" }}>{p.e ? <IcCheck size={13} style={{ color: "oklch(var(--success))" }} /> : <span className="muted">—</span>}</td>
                      <td style={{ textAlign: "center" }}>{p.u ? <IcCheck size={13} style={{ color: "oklch(var(--success))" }} /> : <span className="muted">—</span>}</td>
                      <td style={{ textAlign: "center", opacity: 0.6 }}>{p.w ? <IcCheck size={13} style={{ color: "oklch(var(--success))" }} /> : <span className="muted">—</span>}</td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function GroupsTab() {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Entra ID groups</h3>
          <div className="card-desc">Synced from <span className="mono">ricoh.onmicrosoft.com</span> tenant · group → role mapping in Settings → Identity & Auth</div>
        </div>
        <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> Sync from Entra</button>
      </div>
      <div className="card-body card-body-tight">
        <table className="table">
          <thead><tr><th>Group name</th><th>Object ID</th><th>EKP role</th><th className="col-num">Members</th><th className="col-num">Synced</th><th className="col-shrink"></th></tr></thead>
          <tbody>
            {[
              { name: "grp-ekp-admins",  oid: "a7f4…b1c4", role: "admin",  count: 3,  synced: "2m ago" },
              { name: "grp-ekp-editors", oid: "b9e2…a4d8", role: "editor", count: 12, synced: "2m ago" },
              { name: "grp-ekp-users",   oid: "c1f3…b7e2", role: "user",   count: 28, synced: "2m ago" },
              { name: "grp-ricoh-japan", oid: "d2a8…c4f1", role: "(unmapped)", count: 142, synced: "5m ago" },
            ].map((g) => (
              <tr key={g.name}>
                <td className="col-mono">{g.name}</td>
                <td className="col-mono text-xs">{g.oid}</td>
                <td>{g.role === "(unmapped)" ? <span className="text-xs muted">Not mapped</span> : <RoleBadge role={g.role} />}</td>
                <td className="col-num">{g.count}</td>
                <td className="col-num text-xs">{g.synced}</td>
                <td className="col-shrink"><button className="btn btn-ghost btn-icon btn-xs"><IcMore size={13} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AuditTab() {
  const events = [
    { at: "2 min ago",  actor: "chris.lai",   action: "role.changed",     target: "carlos.r → user",            note: "Demoted from editor" },
    { at: "14 min ago", actor: "chris.lai",   action: "user.invited",     target: "lisa.brown@ricoh.com",       note: "Email invite sent · 7d expiry" },
    { at: "1h ago",     actor: "system",      action: "user.suspended",   target: "james.obrien",                note: "Auto · 90d inactivity policy" },
    { at: "3h ago",     actor: "chris.lai",   action: "kb.access.granted", target: "Drive Manuals → priya.anand", note: "Editor access" },
    { at: "5h ago",     actor: "chris.lai",   action: "provider.key.rotated", target: "Cohere · rerank-v4.0-pro", note: "90d rotation reminder" },
    { at: "Yesterday",  actor: "chris.lai",   action: "kb.config.changed", target: "Customer Service SOP · default_top_k 50 → 30", note: "Editable field · no re-index" },
  ];
  const actionIcon = (a) =>
    a.startsWith("role")        ? IcShield :
    a.startsWith("user")        ? IcUsers :
    a.startsWith("kb.access")   ? IcLink :
    a.startsWith("provider")    ? IcCpu :
    a.startsWith("kb.config")   ? IcEdit :
                                  IcActivity;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Workspace audit log</h3>
          <div className="card-desc">Every role / access / config change is logged with actor + target + timestamp · 90d retention</div>
        </div>
        <div className="row">
          <button className="btn btn-secondary btn-sm"><IcFilter size={13} /> Filter</button>
          <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> Export</button>
        </div>
      </div>
      <div className="card-body card-body-tight">
        {events.map((e, i, arr) => {
          const Ic = actionIcon(e.action);
          return (
            <div key={i} style={{ display: "flex", gap: 12, padding: "12px 18px", borderBottom: i < arr.length - 1 ? "1px solid oklch(var(--border))" : "none" }}>
              <div style={{ width: 26, height: 26, borderRadius: "var(--radius-sm)", background: "oklch(var(--muted))", display: "grid", placeItems: "center", flexShrink: 0 }}>
                <Ic size={13} className="muted" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
                  <span className="mono text-xs" style={{ background: "oklch(var(--muted))", padding: "1px 5px", borderRadius: 3, fontWeight: 600 }}>{e.action}</span>
                  <span className="text-xs muted">by</span>
                  <span className="mono text-xs">{e.actor}</span>
                </div>
                <div style={{ fontSize: 12.5, lineHeight: 1.45 }}>{e.target}</div>
                <div className="text-xs muted" style={{ marginTop: 2 }}>{e.note}</div>
              </div>
              <span className="text-xs muted mono" style={{ flexShrink: 0 }}>{e.at}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Stat({ label, value, sub }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-meta">{sub}</div>
    </div>
  );
}

// ── KB Detail · Access tab — per-KB ACL ────────────────────────────────────
function TabKbAccess({ kb, onNavigate }) {
  return (
    <div>
      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <IcShield size={14} style={{ color: "oklch(var(--info))" }} />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>Per-KB access control</div>
          <div className="text-xs muted">
            Members listed here can query / edit / manage <b>this</b> KB regardless of their workspace role. Workspace Admins always have full access.
          </div>
        </div>
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 16 }}>
        <Stat label="Visibility" value="Workspace" sub="Members of Ricoh · RAPO" />
        <Stat label="Members with access" value="14" sub="3 manage · 4 edit · 7 query" />
        <Stat label="Pending invites" value="0" sub="—" />
        <Stat label="Default new member access" value="Query only" sub="Inherits Workspace role mapping" />
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">Visibility</h3>
            <div className="card-desc">Who can see this KB exists at all</div>
          </div>
        </div>
        <div className="card-body card-body-tight">
          {[
            { id: "private",   icon: IcShield,   label: "Private",          desc: "Only explicit members + Workspace Admins · others can't see this KB", active: false },
            { id: "workspace", icon: IcUsers,    label: "Workspace",        desc: "Any member of Ricoh · RAPO can find + query this KB", active: true },
            { id: "public",    icon: IcGlobe,    label: "Public (Tier 2)",  desc: "Listed in public KB catalog · queryable via anonymous API key", active: false, disabled: true },
          ].map((v, i, arr) => {
            const Ic = v.icon;
            return (
              <div key={v.id} style={{ display: "flex", gap: 12, padding: "12px 18px", borderBottom: i < arr.length - 1 ? "1px solid oklch(var(--border))" : "none", opacity: v.disabled ? 0.5 : 1 }}>
                <input type="radio" name="visibility" defaultChecked={v.active} disabled={v.disabled} style={{ marginTop: 3, flexShrink: 0, accentColor: "oklch(var(--accent))" }} />
                <Ic size={14} className="muted" style={{ marginTop: 3, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontWeight: 500, fontSize: 13.5 }}>{v.label}</span>
                    {v.disabled && <span className="badge badge-muted">Tier 2</span>}
                  </div>
                  <div className="text-xs muted" style={{ marginTop: 2, lineHeight: 1.5 }}>{v.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Members & permissions</h3>
            <div className="card-desc">Per-KB role overrides workspace role · "Manager" can edit access list itself</div>
          </div>
          <div className="row">
            <button className="btn btn-secondary btn-sm"><IcLink size={13} /> Add Entra group</button>
            <button className="btn btn-primary btn-sm"><IcPlus size={13} /> Add member</button>
          </div>
        </div>
        <div className="card-body card-body-tight">
          <table className="table">
            <thead>
              <tr>
                <th>Member / Group</th>
                <th>Workspace role</th>
                <th>KB role</th>
                <th>Granted by</th>
                <th className="col-num">Granted</th>
                <th className="col-shrink"></th>
              </tr>
            </thead>
            <tbody>
              {[
                { kind: "group", name: "grp-ekp-admins",  label: "Workspace Admins (auto)", workspace: "admin",  kb: "manage", granted_by: "system",   granted: "—",        locked: true },
                { kind: "user",  name: "Chris Lai",        email: "chris.lai@ricoh.com",     workspace: "admin",  kb: "manage", granted_by: "system",   granted: "—",        locked: true,  avatar: "CL", you: true },
                { kind: "user",  name: "Priya Anand",      email: "priya.anand@ricoh.com",   workspace: "editor", kb: "manage", granted_by: "chris.lai", granted: "2d ago",  avatar: "PA" },
                { kind: "user",  name: "Daniel Kim",       email: "daniel.kim@ricoh.com",    workspace: "editor", kb: "edit",   granted_by: "chris.lai", granted: "5d ago",  avatar: "DK" },
                { kind: "user",  name: "Mei-Ling Wu",      email: "mei.wu@ricoh.co.jp",      workspace: "editor", kb: "edit",   granted_by: "chris.lai", granted: "1w ago",  avatar: "MW" },
                { kind: "group", name: "grp-ekp-users",    label: "End User group · query access", workspace: "user", kb: "query", granted_by: "chris.lai", granted: "2w ago" },
                { kind: "user",  name: "Carlos Ramirez",   email: "carlos.r@ricoh.com",       workspace: "user",   kb: "query",  granted_by: "(group)",   granted: "(inherited)", inherited: true, avatar: "CR" },
              ].map((m, i, arr) => (
                <tr key={i} style={{ opacity: m.inherited ? 0.75 : 1 }}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      {m.kind === "user" ? (
                        <div className="avatar avatar-sm">{m.avatar}</div>
                      ) : (
                        <div style={{ width: 26, height: 26, borderRadius: "var(--radius-sm)", background: "oklch(var(--muted))", display: "grid", placeItems: "center", flexShrink: 0 }}>
                          <IcLayers size={12} className="muted" />
                        </div>
                      )}
                      <div>
                        <div className="table-row-link" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          {m.kind === "user" ? m.name : <span className="mono">{m.name}</span>}
                          {m.you && <span className="badge badge-accent">YOU</span>}
                        </div>
                        <div className="text-xs muted mono">{m.email || m.label}</div>
                      </div>
                    </div>
                  </td>
                  <td><RoleBadge role={m.workspace} /></td>
                  <td>
                    <select className="select" defaultValue={m.kb} disabled={m.locked || m.inherited} style={{ height: 26, fontSize: 12 }}>
                      <option value="manage">Manager (full)</option>
                      <option value="edit">Editor (upload + tune)</option>
                      <option value="query">Query only</option>
                    </select>
                  </td>
                  <td className="col-mono text-xs">{m.granted_by}</td>
                  <td className="col-num text-xs">{m.granted}</td>
                  <td className="col-shrink">
                    {m.locked ? <span className="badge badge-muted"><IcShield size={9} /> AUTO</span>
                              : <button className="btn btn-ghost btn-icon btn-xs"><IcMore size={13} /></button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <button className="btn btn-ghost btn-xs" style={{ marginTop: 12 }} onClick={() => onNavigate("users")}>
        Manage all workspace members → /users
      </button>
    </div>
  );
}

window.PageUsers = PageUsers;
window.TabKbAccess = TabKbAccess;
window.RoleBadge = RoleBadge;
