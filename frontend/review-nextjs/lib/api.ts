export const BASE_URL =
    process.env.NODE_ENV === "development"
        ? "http://localhost:3000"
        : process.env.NEXT_PUBLIC_BASE_URL!;

export const OIDC_CLIENT_ID = process.env.NEXT_PUBLIC_CLIENT_ID!;
export const OIDC_CLIENT_SECRET = process.env.NEXT_PUBLIC_CLIENT_SECRET!;
export const OIDC_REDIRECT_URI = `${BASE_URL}/callback`;
export const OIDC_AUTHORITY = "https://platform.pennlabs.org";
export const OIDC_AUTHORIZATION_ENDPOINT = `${OIDC_AUTHORITY}/accounts/authorize/`;
export const OIDC_TOKEN_ENDPOINT = `${OIDC_AUTHORITY}/accounts/token/`;
export const JWKS_URI = `${OIDC_AUTHORITY}/accounts/.well-known/jwks.json`;

export const doAPIRequest = (path: string, options = {}): Promise<Response> =>
    fetch(`/api${path}`, options);

export function getLogoutUrl(): string {
    return `/accounts/logout/?next=${encodeURIComponent(`${BASE_URL}/logout`)}`;
}

export function getLoginUrl() {
    return `/accounts/login/?next=${BASE_URL}`;
}
