/* Cliente HTTP de la web: toda escritura se confirma en el backend. */
export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

export function createApi({ base = '', getToken = () => '', onExpired = () => {} } = {}) {
  return async function request(path, { method = 'GET', body, signal } = {}) {
    const headers = { Accept: 'application/json' };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    const timeout = new AbortController();
    const timer = setTimeout(() => timeout.abort(), 15000);
    const abort = () => timeout.abort();
    signal?.addEventListener('abort', abort, { once: true });
    try {
      const response = await fetch(base + path, {
        method, headers, signal: timeout.signal,
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      });
      const data = response.status === 204 ? null : await response.json();
      if (!response.ok) {
        if (response.status === 401 && token && path !== '/auth/login') onExpired();
        const detail = Array.isArray(data?.detail)
          ? data.detail.map(e => `${e.loc.slice(1).join('.')}: ${e.msg}`).join(' · ')
          : data?.detail;
        throw new ApiError(typeof detail === 'string' ? detail : 'No se pudo completar la operación.', response.status);
      }
      return data;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(error.name === 'AbortError' ? 'El servidor tardó demasiado. Vuelve a intentarlo.' : 'No se pudo conectar con el servidor. Revisa tu conexión.', 0);
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
    }
  };
}
