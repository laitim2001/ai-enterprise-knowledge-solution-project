/**
 * CH-013 — cookie-session provider `mapMe()` shape mapping.
 *
 * The backend `GET /auth/me` returns snake_case + a `role` field; the frontend
 * auth-store claim shape is camelCase and carries no role (role is read
 * separately by `useRole()`). This guards that contract translation.
 */

import { describe, expect, it } from 'vitest';

import { _mapMeForTests } from '@/lib/auth/cookie_session';
import type { MeResponse } from '@/lib/api/users';

describe('cookie_session mapMe', () => {
  it('maps the snake_case /auth/me payload onto the camelCase claim shape', () => {
    const me: MeResponse = {
      oid: 'u-abc',
      tid: 't-xyz',
      preferred_username: 'admin@example.com',
      role: 'admin',
      is_mock: false,
    };

    expect(_mapMeForTests(me)).toEqual({
      oid: 'u-abc',
      tid: 't-xyz',
      preferredUsername: 'admin@example.com',
      isMock: false,
    });
  });

  it('preserves is_mock=true → isMock=true', () => {
    const me: MeResponse = {
      oid: 'x',
      tid: 'y',
      preferred_username: 'dev-user@ekp.local',
      role: 'user',
      is_mock: true,
    };

    expect(_mapMeForTests(me).isMock).toBe(true);
  });

  it('drops the role field (the store user shape has no role)', () => {
    const me: MeResponse = {
      oid: 'x',
      tid: 'y',
      preferred_username: 'editor@example.com',
      role: 'editor',
      is_mock: false,
    };

    expect(_mapMeForTests(me)).not.toHaveProperty('role');
  });
});
