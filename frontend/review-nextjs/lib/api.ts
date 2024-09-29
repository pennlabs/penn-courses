const API_DOMAIN = `${window.location.protocol}//${window.location.host}`;

export function getLogoutUrl(): string {
    return `${API_DOMAIN}/accounts/logout/?next=${encodeURIComponent(
      `${window.location.origin}/logout`
    )}`;
}
