import { ComponentType, PropsWithChildren } from "react";

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

export type WrappedStyled<P> = ComponentType<PropsWithChildren<Partial<P>>>;
