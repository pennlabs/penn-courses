"use client"

import { Button } from "@/components/ui/button"
import { signIn, signOut } from "next-auth/react"

export const SignInButton = () => {
	return <Button onClick={() => signIn()}>Sign in</Button>
}

export const SignOutButton = () => {
	return <Button onClick={() => signOut()}>Sign out</Button>
}
