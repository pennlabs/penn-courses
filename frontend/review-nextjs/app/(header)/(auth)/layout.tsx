"use client";

export default function AuthLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return <div className="flex flex-col">{children}</div>;
}
