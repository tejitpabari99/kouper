/**
 * SvelteKit server hook — API reverse proxy.
 *
 * Why this exists: the FastAPI backend runs on localhost:8000 and is never
 * exposed directly to the browser. All frontend API calls go to `/api/*`,
 * and this hook intercepts them server-side, rewrites the URL to the backend,
 * and streams the response back. This avoids CORS issues and keeps the backend
 * address out of client-side code.
 *
 * Any request not matching `/api` falls through to normal SvelteKit routing.
 */
const FASTAPI_URL = 'http://localhost:8000';

export async function handle({ event, resolve }) {
  if (event.url.pathname.startsWith('/api')) {
    // Strip the `/api` prefix to get the actual backend path
    const apiPath = event.url.pathname.replace('/api', '') || '/';
    const target = new URL(apiPath + event.url.search, FASTAPI_URL);

    const reqHeaders = new Headers(event.request.headers);
    // Remove `host` so the backend doesn't get confused by the browser's hostname
    reqHeaders.delete('host');
    // Disable compression so we can forward the raw body without re-decompressing it
    reqHeaders.set('accept-encoding', 'identity');

    try {
      const response = await fetch(target.toString(), {
        method: event.request.method,
        headers: reqHeaders,
        // GET/HEAD have no body; everything else streams the request body through
        body: ['GET', 'HEAD'].includes(event.request.method) ? undefined : event.request.body,
        .../** @type {any} */({ duplex: 'half' }), // required by Node for streaming request bodies
      });

      const resHeaders = new Headers(response.headers);
      // Drop content-encoding — we're passing the raw (already decoded) body
      resHeaders.delete('content-encoding');

      return new Response(response.body, {
        status: response.status,
        headers: resHeaders,
      });
    } catch (e) {
      // Backend is down or unreachable — surface a clean 503 instead of a crash
      return new Response(JSON.stringify({ detail: 'API unavailable' }), {
        status: 503,
        headers: { 'content-type': 'application/json' },
      });
    }
  }
  return resolve(event);
}
