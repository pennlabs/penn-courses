import { NextRequest, NextResponse } from "next/server"
import { checkAuth, } from "./lib/api"

const protectedRoutes = ["/review"]
const publicRoutes = ["/", "/faq", "/about"]

export default async function middleware(req: NextRequest) {
    // 2. Check if the current route is protected or public
    const path = req.nextUrl.pathname
    const isProtectedRoute = protectedRoutes.includes(path)
    const isPublicRoute = publicRoutes.includes(path)
      
    // 4. Redirect to /login if the user is not authenticated
    // if (isProtectedRoute) {
    //     const isAuth = await checkAuth()
    //     if (!isAuth) {
    //         return NextResponse.redirect(new URL(getLoginUrl(), req.nextUrl))
    //     }
    // }
   
    return NextResponse.next()
}