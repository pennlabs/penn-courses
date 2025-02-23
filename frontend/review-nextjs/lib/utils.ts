import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * @returns {string | boolean} The CSRF token used by backend
 */
export const getCsrf = (): string | boolean => {
  return document.cookie &&
    document.cookie
        .split("; ")
        .reduce(
            (acc: string | boolean, cookie) =>
                acc ||
                (cookie.substring(0, "csrftoken".length + 1) ===
                    "csrftoken=" &&
                    decodeURIComponent(
                        cookie.substring("csrftoken=".length)
                    )),
            false
        );
};
