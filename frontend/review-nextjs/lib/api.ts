export const doAPIRequest = (path: string, options = {}): Promise<Response> =>
  fetch(`/api${path}`, options);

export function getLogoutUrl(): string {
  return `/accounts/logout/?next=${encodeURIComponent(
    `${window.location.origin}/logout`
  )}`;
}

export function redirectForAuth(): void {
  window.location.href = `/accounts/login/?next=${encodeURIComponent(
    window.location.pathname
  )}`;
}

export async function apiCheckAuth(): Promise<boolean> {
  const res = await doAPIRequest("/accounts/me/");
  if (res.status < 300 && res.status >= 200) {
    return true;
  } else {
    return false;
  }
}
