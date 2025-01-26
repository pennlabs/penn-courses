export const BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:3000'
  : process.env.NEXT_PUBLIC_BASE_URL;

export const CLIENT_ID = process.env.NEXT_PUBLIC_CLIENT_ID ?? "";
export const CLIENT_SECRET = process.env.NEXT_PUBLIC_CLIENT_SECRET ?? "";

export const doAPIRequest = (path: string, options = {}): Promise<Response> =>
  fetch(`/api${path}`, options);

export function getLogoutUrl(): string {
  return `/accounts/logout/?next=${encodeURIComponent(
    `${BASE_URL}/logout`
  )}`;
}

export function getLoginUrl() {
  return `/accounts/login/?next=${BASE_URL}`;
}
