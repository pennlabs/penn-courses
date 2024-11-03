export const doAPIRequest = (path: string, options = {}): Promise<Response> =>
  fetch(`/api${path}`, options);

export function getLogoutUrl(): string {
  return `/accounts/logout/?next=${encodeURIComponent(
    `${window.location.origin}/logout`
  )}`;
}

export function getLoginUrl() {
  return `/accounts/login/?next=${encodeURIComponent(
      window.location.pathname
  )}`;
}

export async function checkAuth(): Promise<boolean> {
  const res = await fetch("/accounts/me/");
  if (res.status < 300 && res.status >= 200) {
    return true;
  } else {
    return false;
  }
}
