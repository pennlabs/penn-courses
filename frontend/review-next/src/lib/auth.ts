import type {
    GetServerSidePropsContext,
    NextApiRequest,
    NextApiResponse,
  } from "next"
import type { NextAuthOptions } from "next-auth"
import { getServerSession } from "next-auth"

const CLIENT_ID = "client_id"
const CLIENT_SECRET = "supersecretclientsecret"

  export const config = {
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
				url: "http://localhost:8000/accounts/authorize/",
			},
			token: {
				params: { grant_type: "authorization_code" },
				url: "http://localhost:8000/accounts/token/",
			},
			userinfo: "http://localhost:8000/accounts/me/",
			profileUrl: "http://localhost:8000/accounts/me/",
			profile: (profile) => {
				return {
					id: profile.pennid,
					name: profile.username,
					email: profile.email,
				}
			},
		},
	],
  } satisfies NextAuthOptions
  
  // Use it in server contexts
  export function auth(
    ...args:
      | [GetServerSidePropsContext["req"], GetServerSidePropsContext["res"]]
      | [NextApiRequest, NextApiResponse]
      | []
  ) {
    return getServerSession(...args, config)
  }
  
