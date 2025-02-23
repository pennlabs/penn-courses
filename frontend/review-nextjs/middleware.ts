import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import {
    JWKS_URI,
    OIDC_AUTHORIZATION_ENDPOINT,
    OIDC_CLIENT_ID,
    OIDC_REDIRECT_URI,
} from "@/lib/api";
import * as jose from "jose";

interface RawPayload {
    sub: string;
    name: string;
    email: string;
    pennkey: string;
    pennid: number;
    is_staff: boolean;
    is_active: boolean;
}

// cache JWKs so doesn't need to be fetched every time
let jwks: any = null;
async function getJWKSet() {
    if (!jwks) {
        jwks = await jose.createRemoteJWKSet(new URL(JWKS_URI));
    }
    return jwks;
}

export async function middleware(request: NextRequest) {
    const id_token = request.cookies.get("id_token")?.value;

    if (id_token) {
        // Verify access_token
        const jwks = await getJWKSet();
        try {
            const { payload } = await jose.jwtVerify<RawPayload>(
                id_token,
                jwks,
                {
                    clockTolerance: "1m",
                }
            );
            return NextResponse.next();
        } catch (e) {}
    }

    // Request authorization code
    const authorizationUrl = new URL(OIDC_AUTHORIZATION_ENDPOINT);
    authorizationUrl.searchParams.set("client_id", OIDC_CLIENT_ID);
    authorizationUrl.searchParams.set("redirect_uri", OIDC_REDIRECT_URI);
    authorizationUrl.searchParams.set("response_type", "code");
    authorizationUrl.searchParams.set("scope", "openid read");

    return NextResponse.redirect(authorizationUrl.toString());
}

export const config = {
    matcher: "/review/:path",
};
