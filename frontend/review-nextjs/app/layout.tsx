import type { Metadata } from "next";
import "./globals.css";
import { cn } from "@/lib/utils";
import { AuthProvider } from "react-oidc-context";
import Footer from "../components/Footer";

export const metadata: Metadata = {
    title: "Penn Course Review",
    description: "Made by Penn Labs",
};

const oidcConfig = {
    authority: "<your authority>",
    clientId: "<your client id>",
    redirectUri: "<your redirect uri>",
    // ...
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={cn("antialiased", "flex", "flex-col")}>
                <AuthProvider {...oidcConfig}>
                    {children}
                    <Footer />
                </AuthProvider>
            </body>
        </html>
    );
}
