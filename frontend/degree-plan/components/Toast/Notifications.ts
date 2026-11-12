import { createContext } from "react";

export interface Notification {
  id: number;
  message: string;
  error: boolean;
  createdAt: number;
  read: boolean;
}

export const NotificationsContext = createContext<{
  notifications: Notification[];
  markAllRead: () => void;
  clear: () => void;
}>({ notifications: [], markAllRead: () => {}, clear: () => {} });

export const MAX_NOTIFICATIONS = 50;
