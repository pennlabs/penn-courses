import {
    OIDC_TOKEN_ENDPOINT,
    OIDC_CLIENT_ID,
    OIDC_REDIRECT_URI,
    OIDC_CLIENT_SECRET,
} from "@/lib/api";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
    const code = request.nextUrl.searchParams.get("code");
    if (!code) {
        throw new Error("Platform Authentication Failed");
    }

    const res = await fetch(OIDC_TOKEN_ENDPOINT, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            grant_type: "authorization_code",
            client_id: OIDC_CLIENT_ID,
            client_secret: OIDC_CLIENT_SECRET,
            redirect_uri: OIDC_REDIRECT_URI,
            code,
        }).toString(),
    });

    if (!res.ok) {
        throw new Error("Platform Authentication Failed");
    }

    const tokens = await res.json();

    const response = NextResponse.redirect(new URL("/review", request.url));
    response.cookies.set("id_token", tokens.id_token, {
        httpOnly: true,
        secure: true,
    });
    response.cookies.set("access_token", tokens.access_token, {
        httpOnly: true,
        secure: true,
    });

    return response;
}
