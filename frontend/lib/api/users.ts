/**
 * Users / RBAC API client (W24c F9 per ADR-0027 Option A).
 *
 * Wraps the F4 (`/users/*`) + F5 (`/roles*`) + F6 (`/groups*`) endpoints that
 * surface the `/users` 4-tab page per mockup `ekp-page-users.jsx`, plus the
 * F9.1 `GET /auth/me` current-user read that powers `useRole()`.
 *
 * Field names mirror the backend Pydantic models (snake_case) — see
 * `backend/api/schemas/user.py` (F4) + `backend/api/schemas/rbac.py` (F5/F6).
 */

import { ApiClient } from '../api-client';
import type { EkpRoleKey } from './admin';

const client = new ApiClient();

// ---------- F9.1 — GET /auth/me ----------------------------------------------

/** `GET /auth/me` — the authenticated caller's identity + RBAC role. */
export interface MeResponse {
  oid: string;
  tid: string;
  preferred_username: string;
  role: EkpRoleKey;
  is_mock: boolean;
}

// ---------- F4 — /users Members tab ------------------------------------------

/** `pending` is derived (email unverified); the rest map to `UserRecord.status`. */
export type UserDisplayStatus = 'active' | 'pending' | 'invited' | 'suspended';

export interface UserSummary {
  oid: string;
  email: string;
  display_name: string;
  role: EkpRoleKey;
  status: UserDisplayStatus;
  created_at: string;
}

export interface UserListResponse {
  users: UserSummary[];
  total: number;
}

export interface InviteRequest {
  email: string;
  role?: EkpRoleKey;
  display_name?: string | null;
}

// ---------- F5 — /roles Roles tab --------------------------------------------

export interface Role {
  role_key: EkpRoleKey;
  label: string;
  description: string;
  tier: number;
  active: boolean;
}

export interface RoleListResponse {
  roles: Role[];
  total: number;
}

export interface RolePermission {
  role_key: EkpRoleKey;
  permission_key: string;
  area: string;
  label: string;
  granted: boolean;
}

export interface PermissionMatrixResponse {
  permissions: RolePermission[];
  total: number;
}

// ---------- F6 — /groups Groups tab ------------------------------------------

export type GroupSource = 'local' | 'entra';

export interface Group {
  group_key: string;
  name: string;
  description: string | null;
  source: GroupSource;
  entra_object_id: string | null;
  synced_at: string | null;
  member_count: number;
}

export interface GroupListResponse {
  groups: Group[];
  total: number;
}

export interface GroupSyncResult {
  status: 'synced' | 'skipped';
  synced_count: number;
  detail: string;
}

// ---------- ApiClient surface ------------------------------------------------

export const usersApi = {
  // F9.1 — current user (role for useRole())
  getMe: (): Promise<MeResponse> => client.get('/auth/me'),

  // F4 — Members tab
  listUsers: (): Promise<UserListResponse> => client.get('/users'),
  inviteUser: (body: InviteRequest): Promise<UserSummary> =>
    client.post('/users/invite', body),
  suspendUser: (oid: string): Promise<UserSummary> =>
    client.post(`/users/${oid}/suspend`, {}),
  changeUserRole: (oid: string, role: EkpRoleKey): Promise<UserSummary> =>
    client.patch(`/users/${oid}/role`, { role }),

  // F5 — Roles tab
  listRoles: (): Promise<RoleListResponse> => client.get('/roles'),
  listPermissions: (): Promise<PermissionMatrixResponse> =>
    client.get('/roles/permissions'),

  // F6 — Groups tab
  listGroups: (): Promise<GroupListResponse> => client.get('/groups'),
  syncGroupsFromEntra: (): Promise<GroupSyncResult> =>
    client.post('/groups/sync-from-entra', {}),
};
