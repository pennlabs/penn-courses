import { ComponentType, HTMLAttributes, PropsWithChildren } from "react";

export interface Profile {
    email: string | null;
    phone: string | null;
}

export interface User {
    username: string;
    first_name: string;
    last_name: string;
    profile: Profile;
}

export type WrappedStyled<P, E = HTMLDivElement> = ComponentType<
    PropsWithChildren<P & HTMLAttributes<E>>
>;
