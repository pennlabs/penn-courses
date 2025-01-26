import { CLIENT_ID, CLIENT_SECRET } from "@/lib/api";
import NextAuth from "next-auth";

const handler = NextAuth({
    providers: [
        {
            id: "pennlabs",
            name: "Penn Labs",
            type: "oauth",
            version: "2.0",
            clientId: CLIENT_ID,
            clientSecret: CLIENT_SECRET,
            authorization: {
                params: {
                    response_type: "code",
                    scope: "read",
                },
                url: "https://platform.pennlabs.org/accounts/authorize/",
            },
            token: {
                params: { grant_type: "authorization_code" },
                url: "https://platform.pennlabs.org/accounts/token/",
            },
            userinfo: "https://platform.pennlabs.org/accounts/me/",
            profileUrl: "https://platform.pennlabs.org/accounts/me/",
            profile: (profile) => {
                return {
                    id: profile.pennid,
                    name: profile.username,
                    email: profile.email,
                }
            }
        }
    ],
    pages: {
        signIn: "/auth/signin",
        signOut: "/auth/signout",
        error: "/auth/error",
        verifyRequest: "/auth/verify-request",
    },
})

export { handler as GET, handler as POST };
