import { NextRequest } from "next/server";
import { cookies } from "next/headers";

export async function GET(request: NextRequest) {
    const cookie_store = await cookies();
    const access_token = cookie_store.get("access_token")?.value;

    const response = await fetch(new URL("/accounts/me", request.url), {
        headers: {
            Authorization: `Bearer ${access_token}`,
            "Access-Control-Allow-Origin": "*",
        },
    });
    console.log(response);

    return Response.json({ data: response.json() });
}
