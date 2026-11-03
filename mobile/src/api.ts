/** Transporte nativo: errores legibles, tiempo límite y token por conexión. */
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = 'copa-token';
export const URL_KEY = 'copa-api-url';
export class ApiError extends Error {
  constructor(message:string, public status:number) { super(message); }
}
export function normalizeUrl(value:string):string {
  const url = new URL(value.trim());
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('Usa la dirección del servidor, por ejemplo http://192.168.1.54:8001');
  }
  return url.origin;
}
export const tokenStore = {
  get: () => Platform.OS === 'web' ? Promise.resolve(sessionStorage.getItem(TOKEN_KEY)) : SecureStore.getItemAsync(TOKEN_KEY),
  set: (token:string) => Platform.OS === 'web' ? Promise.resolve(sessionStorage.setItem(TOKEN_KEY,token)) : SecureStore.setItemAsync(TOKEN_KEY,token),
  clear: () => Platform.OS === 'web' ? Promise.resolve(sessionStorage.removeItem(TOKEN_KEY)) : SecureStore.deleteItemAsync(TOKEN_KEY),
};
export { AsyncStorage };

export async function request<T>(base:string, path:string, token='', method='GET', body?:unknown):Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const headers:Record<string,string> = { Accept:'application/json' };
    if (token) headers.Authorization = 'Bearer ' + token;
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    const response = await fetch(base + path,{method,headers,signal:controller.signal,...(body !== undefined ? {body:JSON.stringify(body)} : {})});
    const data = response.status === 204 ? null : await response.json();
    if (!response.ok) {
      const detail = Array.isArray(data?.detail) ? data.detail.map((e:{loc:string[];msg:string}) => e.loc.slice(1).join('.') + ': ' + e.msg).join(' · ') : data?.detail;
      throw new ApiError(typeof detail === 'string' ? detail : 'No se pudo completar la operación.',response.status);
    }
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('No se pudo conectar. Comprueba la dirección del backend y que el teléfono y el PC estén en la misma red Wi-Fi.',0);
  } finally { clearTimeout(timer); }
}
