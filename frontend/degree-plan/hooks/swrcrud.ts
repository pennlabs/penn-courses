import { DBObject } from "@/types";
import useSWR, { useSWRConfig } from "swr";

// TODO: this is copied from alert and plan, we should move it to a shared location
/**
 * @returns {string | boolean} The CSRF token used by the Django REST Framework
 */
const getCsrf = (): string | boolean => {
    const result =
        document.cookie &&
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
    return result;
};

export const getFetcher = (resource: string) => fetch(resource, {
    method: "GET",
    credentials: "include",
    mode: "same-origin",
    headers: {
        "Accept": "application/json",
        "X-CSRFToken": getCsrf(),
    } as HeadersInit, // TODO: idk if this is a good cast
}).then(res => res.json());

export const postFetcher = (resource: string, body: any) => fetch(resource, {
    method: "POST",
    credentials: "include",
    mode: "same-origin",
    headers: {
        "Accept": "application/json",
        "X-CSRFToken": getCsrf(),
        "Content-Type": "application/json"
    } as HeadersInit,
    body: JSON.stringify(body)
}).then(res => res.json());

export const patchFetcher = (resource: string, body: any) => fetch(resource, {
    method: "PATCH",
    credentials: "include",
    mode: "same-origin",
    headers: {
        "Accept": "application/json",
        "X-CSRFToken": getCsrf(),
        "Content-Type": "application/json"
    } as HeadersInit,
    body: JSON.stringify(body)
}).then(res => res.json());

export const deleteFetcher = (resource: string) => fetch(resource, {
    method: "DELETE",
    credentials: "include",
    mode: "same-origin",
    headers: {
        "Accept": "application/json",
        "X-CSRFToken": getCsrf(),
    } as HeadersInit,
});

const normalizeFinalSlash = (resource: string) => {
    if (!resource.endsWith("/")) resource += "/";
    return resource
}


export const useSWRCrud = <T extends DBObject,>(
    endpoint: string, 
    config = {}
) => {
    const { createFetcher, updateFetcher, removeFetcher } = {
        createFetcher: postFetcher, 
        updateFetcher: patchFetcher, 
        removeFetcher: deleteFetcher, 
        ...config
    }

    const { mutate } = useSWRConfig();

    const create = (newItem: any) => {
        const new_ = createFetcher(endpoint, newItem);
        mutate(endpoint, new_, {
            optimisticData: (list?: Array<T>) => list ? [...list, newItem] : [newItem],
            populateCache: (new_: T, list?: Array<T>) => list ? [...list, new_] : [new_],
            revalidate: false
        })

        return new_;
    }

    const update = (updatedData: Partial<T>, id: string | Number | undefined) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id;
        const updated = updateFetcher(key, updatedData);
        mutate(key, updated, {
            optimisticData: (data?: T) => ({ id: -1, ...data, ...updatedData} as T), // TODO: this is hacky
            revalidate: false
        })

        mutate(endpoint, updated, {
            optimisticData: (list?: Array<T>) => {
                if (!list) return [];
                const index = list.findIndex((item: T) => String(item.id) === id);
                if (index === -1) {
                    mutate(endpoint) // trigger revalidation
                    return list;
                }
                list.splice(index, 1, {...list[index], ...updatedData});
                return list;
            },
            populateCache: (updated: T, list?: Array<T>) => {
                if (!list) return [];
                const index = list.findIndex((item: T) => item.id === updated.id);
                if (index === -1) {
                    console.error("swrcrud: update: updated element not found in list view");
                    mutate(endpoint); // trigger revalidation
                    return list;
                }
                list.splice(index, 1, updated);
                return list
            },
            revalidate: false,
        })

        return updated;
    }

    const remove = (id: Number | string | undefined) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id;
        const removed = removeFetcher(key);
        mutate(endpoint, removed, {
            optimisticData: (list?: Array<T>) => list ? list.filter((item: T) => String(item.id) !== id) : [],
            populateCache: (_, list?: Array<T>) => list ? list.filter((item: any) => item.id !== id) : [],
            revalidate: false
        })
        mutate(key, removed, {
            optimisticData: () => undefined,
            populateCache: () => undefined,
            revalidate: false
        })

        return removed;
    }

    return { create, update, remove };
}

interface SWRCreate<T> {
    data: T[] | undefined;
    error: any;
    create: (newItem: Partial<T>) => void; 
    isLoading: boolean;
    isValidating: boolean;
}

interface SWRCrud<T> {
    data: T | undefined;
    error: any;
    isLoading: boolean;
    isValidating: boolean;
    create: (newItem: Partial<T>) => void;
    update: (updatedData: Partial<T>) => void;
    remove: () => void;
}


/**
 * useSWR wrapper for RESTful list endpoints (e.g., /api/degree/degreeplans)
 * This function will postpend a trailing slash if it is not present.
 * @template T the type of data listed by the endpoint (i.e., DegreePlan not DegreePlan[]) 
 * @param endpoint the endpoint (e.g., /api/degree/degreeplans/)
 * @returns the typical data and error swr returns, plus a create function
 * which replaces the mutate function from swr.
 */
export const useSWRListCreate = <T extends DBObject,>(endpoint: string): SWRCreate<T> => {
    const { data, error, isLoading, isValidating, mutate } = useSWR(endpoint, getFetcher);

    const create = (newItem: any) => {
        const new_ = postFetcher(endpoint, newItem);
        mutate(new_, {
            optimisticData: (list: Array<T>) => list ? [...list, newItem] : [newItem],
            populateCache: (new_: T, list: Array<T>) => [...list, new_],
            rollbackOnError: (e) => {
                console.error(e);
                return true;
            },
            revalidate: false,
        })
    }

    return { data, error, create, isLoading, isValidating };
}