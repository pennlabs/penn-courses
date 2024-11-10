"use client";
import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import { BASE_URL, CLIENT_ID } from "@/lib/api";

export const userManager = new UserManager({
    authority: "https://platform.pennlabs.org/",
    client_id: CLIENT_ID,
    redirect_uri: `${BASE_URL}/callback`,
    scope: "openid read",
    metadataUrl:
        "https://platform.pennlabs.org/accounts/.well-known/openid-configuration/",
    metadata: {
        authorization_endpoint:
            "https://platform.pennlabs.org/accounts/authorize/",
        token_endpoint: "https://platform.pennlabs.org/accounts/token/",
        jwks_uri:
            "https://platform.pennlabs.org/accounts/.well-known/jwks.json",
    },
    automaticSilentRenew: true,
    includeIdTokenInSilentRenew: true,
    userStore: new WebStorageStateStore({ store: window?.localStorage }),
});
console.log(userManager);
