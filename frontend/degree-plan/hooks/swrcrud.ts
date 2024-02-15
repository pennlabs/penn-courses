import { DBObject, assertValueType } from "@/types";
import { assert } from "console";
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

export const useSWRCrud = <T extends DBObject, idType = Number | string | null>(
    endpoint: string, 
    config = {}
) => {
    const { createFetcher, updateFetcher, removeFetcher, createOrUpdateFetcher, idKey } = {
        createFetcher: postFetcher, 
        updateFetcher: patchFetcher, 
        removeFetcher: deleteFetcher, 
        createOrUpdateFetcher: postFetcher,
        idKey: "id" as keyof T ,
        ...config
    }

    const { mutate } = useSWRConfig();

    const create = (newItem: any) => {
        const created = createFetcher(endpoint, newItem);
        mutate(endpoint, created, {
            optimisticData: (list?: Array<T>) => list ? [...list, newItem] : [newItem],
            populateCache: (created: T, list?: Array<T>) => list ? [...list, created] : [created],
            revalidate: false
        })

        return created;
    }

    const update = (updatedData: Partial<T>, id: idType) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id;
        const updated = updateFetcher(key, updatedData);
        mutate(key, updated, {
            optimisticData: (data?: T) => {
                const optimistic = {...data, ...updatedData} as T;
                assertValueType(optimistic, idKey, id)
                optimistic[idKey] = id;
                return ({ id, ...data, ...updatedData} as T)
            },
            revalidate: false
        })

        mutate(endpoint, updated, {
            optimisticData: (list?: Array<T>) => {
                if (!list) return [];
                const index = list.findIndex((item: T) => String(item[idKey]) === id);
                if (index === -1) {
                    mutate(endpoint) // trigger revalidation
                    return list;
                }
                list.splice(index, 1, {...list[index], ...updatedData});
                return list;
            },
            populateCache: (updated: T, list?: Array<T>) => {
                if (!list) return [];
                const index = list.findIndex((item: T) => item[idKey] === updated[idKey]);
                if (index === -1) {
                    console.warn("swrcrud: update: updated element not found in list view");
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

    const remove = (id: idType) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id;
        const removed = removeFetcher(key);
        mutate(endpoint, removed, {
            optimisticData: (list?: Array<T>) => list ? list.filter((item: T) => String(item[idKey]) !== id) : [],
            populateCache: (_, list?: Array<T>) => list ? list.filter((item: any) => item[idKey] !== id) : [],
            revalidate: false
        })
        mutate(key, removed, {
            optimisticData: () => undefined,
            populateCache: () => undefined,
            revalidate: false
        })

        return removed;
    }

    const createOrUpdate = (data: Partial<T>, id: any) => {
        if (!id) return;
        const updated: Partial<T> = {...data}
        updated[idKey] = id;
        mutate(
            endpoint,
            postFetcher(endpoint, updated), 
            {
                optimisticData: (list: Array<T> | undefined) => {
                    if (!list) return [];
                    const old = list.find((item: T) => item[idKey] === id) || {};
                    const optimistic = {...old, ...updated} as T;
                    return [...list.filter((item: T) => item[idKey] !== id), optimistic]
                },
                populateCache: (updated: T, list: Array<T> | undefined) => {
                    if (!list) return [updated];
                    return [...list.filter((item: T) => item[idKey] !== id), updated]
                },
                revalidate: false,
            }
        )
    }
    
    return { create, update, remove, createOrUpdate };
}

const useSWRCreateOrUpdate = <T extends DBObject>(endpoint: string, config = {}) => {
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