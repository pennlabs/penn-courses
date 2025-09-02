import pako from "pako";
import { getAutocomplete, setAutocomplete } from "@/lib/autocomplete";
import { AutocompleteData } from "@/lib/types";

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
export const currentSemester = "2025A";

export const apiFetch = (path: string, options = {}): Promise<Response> =>
    fetch(`${BASE_URL}${path}`, {
        ...options,
        credentials: "include",
    });

// Stale while revalidate strategy:
// decompress and use potentially stale autocomplete data from localstorage
// while asynchronously revalidating by fetching and compressing data
export const apiAutocomplete = async (): Promise<AutocompleteData | null> => {
    const revalidateAutocomplete = async (): Promise<AutocompleteData | null> => {
        try {
            const res = await apiFetch("/api/review/autocomplete");
            const fresh: AutocompleteData = await res.json();
            const compressed = pako.gzip(JSON.stringify(fresh));
            await setAutocomplete(compressed);
            return fresh;
        } catch (e) {
            console.error("Failed to refresh autocomplete data", e);
            return null;
        }
    };

    const cached = await getAutocomplete();
    if (cached) {
        try {
            const decompressed: AutocompleteData = JSON.parse(pako.ungzip(cached, { to: "string" }));
            // Trigger background refresh
            revalidateAutocomplete();
            return decompressed;
        } catch (e) {
            console.error("Failed to decompress cached autocomplete data", e);
        }
    }

    const fresh = await revalidateAutocomplete();
    return fresh;
};

export const apiReviewData = async (
    type: string,
    code: string
): Promise<Response> => {
    // return apiFetch(`/api/review/${type}/${code}?semester=${currentSemester}`);
    return apiFetch(`/api/review/${type}/${code}`);
};

export const apiJWT = async (): Promise<Response> => {
    return apiFetch(`/api/review/jwt`);
};
