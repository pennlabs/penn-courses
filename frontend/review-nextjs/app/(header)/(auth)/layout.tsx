"use client";
import Skeleton from "@/components/Skeleton";
import { userManager } from "@/lib/auth";
import { useEffect } from "react";
import { AuthProvider, AuthProviderProps, useAuth } from "react-oidc-context";
import { permanentRedirect } from "next/navigation";

const config = {
    userManager,
    onSigninCallback: (user) => {
        console.log(user);
        permanentRedirect("/review");
    },
} satisfies AuthProviderProps;

export default function AuthLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return <AuthProvider {...config}>{children}</AuthProvider>;
}
