import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
 
// This function can be marked `async` if using `await` inside
export function middleware(request: NextRequest) {
  const sessionid = request.cookies.get('sessionid')?.value;
  const csrftoken = request.cookies.get('csrftoken')?.value;
  if (!sessionid || !csrftoken) {
    return NextResponse.redirect(new URL(`/accounts/login/?next=${request.nextUrl.pathname}`, request.url));
  }
  return NextResponse.next();
}
 
// See "Matching Paths" below to learn more
export const config = {
  matcher: '/review',
}
