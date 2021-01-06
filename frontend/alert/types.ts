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

// Enums for AlertItem component
export enum AlertAction {
    RESUBSCRIBE,
    CANCEL,
    DELETE,
}

export enum SectionStatus {
    CLOSED = "C",
    OPEN = "O",
    CANCELLED = "X",
}

export enum AlertRepeat {
    INACTIVE,
    EOS,
    ONCE,
}

export interface Alert {
    id: number;
    originalCreatedAt: string;
    section: string;
    alertLastSent: string;
    status: SectionStatus;
    repeat: AlertRepeat;
    actions: AlertAction;
}

export interface Instructor {
    id: number;
    name: string;
}

export interface Section {
    section_id: string;
    status: SectionStatus;
    activity: string;
    meeting_times: string;
    instructors: Instructor[];
    course_title: string;
}

export type WrappedStyled<P, E = HTMLDivElement> = ComponentType<
    PropsWithChildren<P & HTMLAttributes<E>>
>;

export type TAlertSel = { [key: number]: boolean };
