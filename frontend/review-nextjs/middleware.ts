import { withAuth } from "next-auth/middleware";
import { redirect } from "next/dist/server/api-utils";
import { NextResponse } from "next/server";

export default withAuth(
  // only executed after authentications
  function middleware(req) {
    console.log(req);
  },
  {
  pages: {
    signIn: "/accounts/login",
    signOut: "/accounts/logout",
    error: "/auth/error",
    verifyRequest: "/auth/verify-request",
  },
  callbacks: {
    authorized({ req, token }) {
      console.log(req)
      return !!token;
    },
  }
});

export const config = {
  matcher: ["/review"],
}
