/**
 * /api/backend/[...path] — Server-side proxy to backend (NEXT_PUBLIC_API_URL).
 *
 * Replaces the next.config.mjs rewrite (Next.js built-in undici proxy whose
 * TLS context we cannot configure). Necessary because Ricoh corp MITM proxy
 * presents a cert signed by Ricoh CA — present in Windows truststore (browser
 * / curl --ssl-no-revoke OK) but NOT in Node's bundled CA list (W11 D2 R8
 * manifestation: undici "SELF_SIGNED_CERT_IN_CHAIN" on built-in proxy fetch).
 *
 * Dev (NODE_ENV !== 'production'): rejectUnauthorized=false skips cert verify
 * for corp proxy MITM bypass.
 * Prod (NODE_ENV='production'): rejectUnauthorized=true — production deploys
 * cloud-to-cloud with no MITM proxy in the path, so default verification works.
 *
 * Streams upstream response body via ReadableStream so /query/stream SSE works.
 */
import { NextRequest } from 'next/server';
import { Agent, request as httpsRequest } from 'node:https';
import { request as httpRequest } from 'node:http';

export const dynamic = 'force-dynamic';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const isDev = process.env.NODE_ENV !== 'production';

const httpsAgent = new Agent({ rejectUnauthorized: !isDev });

// Hop-by-hop headers (RFC 7230 §6.1) + Next.js internal forwarding headers
// must NOT be forwarded — they belong to the immediate connection.
const HOP_HEADERS = new Set([
  'host',
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'x-forwarded-for',
  'x-forwarded-host',
  'x-forwarded-port',
  'x-forwarded-proto',
]);

async function proxy(
  req: NextRequest,
  ctx: { params: { path: string[] } },
): Promise<Response> {
  const path = ctx.params.path.join('/');
  const targetUrl = new URL(`/${path}${req.nextUrl.search}`, BACKEND_URL);

  const headers: Record<string, string> = {};
  req.headers.forEach((value, key) => {
    if (!HOP_HEADERS.has(key.toLowerCase())) headers[key] = value;
  });

  // BUG-013 — In mock-auth dev mode, browser-native subresource requests
  // (<img>, <video>) can't add an Authorization header and the mock flow
  // never sets the ekp_session cookie (mock_msal.ts hardcodes a Bearer
  // in-memory with no /auth/login round-trip). Auto-inject the dev Bearer
  // at the server-side proxy so browser-native requests still authenticate.
  // Production (isDev=false): no injection — real MSAL Bearer / cookie
  // flow through unchanged.
  if (isDev && !headers['authorization']) {
    const devBearer = process.env.NEXT_PUBLIC_AUTH_MOCK_BEARER ?? 'dev-token';
    headers['authorization'] = `Bearer ${devBearer}`;
  }

  // Buffer body for non-GET/HEAD. Streaming the request body would require
  // chunked transfer + duplex 'half' handling; FormData uploads in Tier 1
  // are infrequent + small, buffering is acceptable.
  const body = ['GET', 'HEAD'].includes(req.method)
    ? undefined
    : Buffer.from(await req.arrayBuffer());

  const requester =
    targetUrl.protocol === 'https:' ? httpsRequest : httpRequest;
  const opts: Record<string, unknown> = {
    method: req.method,
    headers,
  };
  if (targetUrl.protocol === 'https:') {
    opts.agent = httpsAgent;
  }

  return new Promise<Response>((resolve, reject) => {
    const upstreamReq = requester(targetUrl, opts, (upstreamRes) => {
      const responseHeaders = new Headers();
      for (const [k, v] of Object.entries(upstreamRes.headers)) {
        if (v == null || HOP_HEADERS.has(k.toLowerCase())) continue;
        if (Array.isArray(v)) {
          v.forEach((vv) => responseHeaders.append(k, vv));
        } else {
          responseHeaders.set(k, v);
        }
      }
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          upstreamRes.on('data', (chunk: Buffer) => controller.enqueue(chunk));
          upstreamRes.on('end', () => controller.close());
          upstreamRes.on('error', (err) => controller.error(err));
        },
        cancel() {
          upstreamRes.destroy();
        },
      });
      resolve(
        new Response(stream, {
          status: upstreamRes.statusCode ?? 502,
          statusText: upstreamRes.statusMessage ?? '',
          headers: responseHeaders,
        }),
      );
    });
    upstreamReq.on('error', reject);
    if (body) upstreamReq.write(body);
    upstreamReq.end();
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
export const HEAD = proxy;
