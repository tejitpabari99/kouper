const FASTAPI_URL = 'http://localhost:8000';

export async function handle({ event, resolve }) {
  if (event.url.pathname.startsWith('/api')) {
    const apiPath = event.url.pathname.replace('/api', '') || '/';
    const target = new URL(apiPath + event.url.search, FASTAPI_URL);
    const reqHeaders = new Headers(event.request.headers);
    reqHeaders.delete('host');
    reqHeaders.set('accept-encoding', 'identity');
    try {
      const response = await fetch(target.toString(), {
        method: event.request.method,
        headers: reqHeaders,
        body: ['GET', 'HEAD'].includes(event.request.method) ? undefined : event.request.body,
        .../** @type {any} */({ duplex: 'half' }),
      });
      const resHeaders = new Headers(response.headers);
      resHeaders.delete('content-encoding');
      return new Response(response.body, {
        status: response.status,
        headers: resHeaders,
      });
    } catch (e) {
      return new Response(JSON.stringify({ detail: 'API unavailable' }), {
        status: 503,
        headers: { 'content-type': 'application/json' },
      });
    }
  }
  return resolve(event);
}
