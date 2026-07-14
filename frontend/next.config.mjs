import createNextIntlPlugin from 'next-intl/plugin';

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Backend proxy moved to app/api/backend/[...path]/route.ts (W11 D2 cont
  // 2026-06-10). The route handler controls TLS settings (required for
  // dev workstations behind Ricoh corp MITM proxy: Node's bundled CA list
  // doesn't include Ricoh CA → undici rewrite proxy throws
  // SELF_SIGNED_CERT_IN_CHAIN). Custom route uses node:https with
  // rejectUnauthorized=false in dev only (prod cloud-to-cloud no MITM).
};

// next-intl plugin — wires i18n/request.ts (cookie-based locale, W103 F3,
// D-2 甲: without i18n routing, so URLs stay flat). ADR-0075 / H2.
const withNextIntl = createNextIntlPlugin();

export default withNextIntl(nextConfig);
