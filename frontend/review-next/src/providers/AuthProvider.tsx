"use client"

import { SessionProvider } from "next-auth/react"
import { PropsWithChildren } from "react"

const AuthProvider: React.FC<PropsWithChildren> = ({ children }) => {
	return <SessionProvider basePath="/auth">{children}</SessionProvider>
}

export default AuthProvider
