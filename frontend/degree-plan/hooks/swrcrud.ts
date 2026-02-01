import { DBObject, assertValueType } from "@/types";
import { assert } from "console";
import useSWR, { useSWRConfig } from "swr";
import { updateDecorator } from "typescript";

interface SWRCrudError extends Error {
    info: any;
    status: number;
}

// TODO: this is copied from alert and plan, we should move it to a shared location
/**
 * @returns {string | boolean} The CSRF token used by the Django REST Framework
 */
export const getCsrf = (): string | boolean => {
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
                            cookie.substring("csrftoken=".length),
                        )),
                false,
            );
    return result;
};

/**
 * The base fetcher for swrcrud.
 * @param init A RequestInit object. By default, the credentials, mode, and headers options are set.
 * @param returnJson Whether to jsonify the response. If this is false, then the function will return
 * undefined
 * @returns JSON or undefined (see @param returnJson).
 */
export const baseFetcher = (
    init: RequestInit,
    returnJson: boolean = true,
) => async (resource: string, body?: any) => {
    const res = await fetch(resource, {
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "X-CSRFToken": getCsrf(),
            "Content-Type": "application/json",
        } as HeadersInit,
        ...init,
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
        const error = new Error(
            "An error occurred while fetching the data.",
        ) as SWRCrudError;
        // Attach extra info to the error object.
        error.info = await res.json();
        error.status = res.status;
        // TODO: need to figure out how to catch these errors
        throw error;
    } else return returnJson ? res.json() : undefined;
};

export const getFetcher = baseFetcher({ method: "GET" });
export const postFetcher = baseFetcher({ method: "POST" });
export const patchFetcher = baseFetcher({ method: "PATCH" });
export const putFetcher = baseFetcher({ method: "PUT" });
export const deleteFetcher = baseFetcher({ method: "DELETE" }, false); // expect no response from delete requests

const normalizeFinalSlash = (resource: string) => {
    if (!resource.endsWith("/")) resource += "/";
    return resource;
};

export const useSWRCrud = <T extends DBObject, idType = Number | string | null>(
    endpoint: string,
    config = {},
) => {
    const {
        createFetcher,
        updateFetcher,
        removeFetcher,
        createOrUpdateFetcher,
        copyFetcher,
        idKey,
        createDefaultOptimisticData,
    } = {
        createFetcher: postFetcher,
        copyFetcher: postFetcher,
        updateFetcher: patchFetcher,
        removeFetcher: deleteFetcher,
        createOrUpdateFetcher: postFetcher,
        idKey: "id" as keyof T,
        createDefaultOptimisticData: {} as Partial<T>, // e.g., for fields computed by the backend
        ...config,
    };

    const { mutate } = useSWRConfig();

    const create = (newItem: Partial<T>) => {
        const created = createFetcher(endpoint, newItem);
        const optimistic = { ...createDefaultOptimisticData, ...newItem } as T;
        mutate(endpoint, created, {
            optimisticData: (list?: Array<T>) =>
                list ? [...list, optimistic] : [optimistic],
            populateCache: (created: T, list?: Array<T>) =>
                list ? [...list, created] : [created],
            revalidate: false,
        });

        return created;
    };

    const copy = (optimisticData: T, id: idType) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id + "/copy"; // assume copy endpoint is `${listEndpoint}/${id}/copy`
        const copied = copyFetcher(key, optimisticData); // the copy endpoint will pull out whatever data it needs
        mutate(endpoint, copied, {
            optimisticData: (list?: Array<T>) =>
                list ? [...list, optimisticData] : [optimisticData],
            populateCache: (copied: T, list?: Array<T>) => {
                if (!copied) return list || [];
                return list ? [...list, copied] : [copied];
            },
            throwOnError: false,
            revalidate: false,
        });
        return copied;
    };

    const update = (updatedData: Partial<T>, id: idType) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id;
        const updated = updateFetcher(key, updatedData);
        mutate(key, updated, {
            optimisticData: (data?: T) => {
                const optimistic = { ...data, ...updatedData } as T;
                assertValueType(optimistic, idKey, id);
                optimistic[idKey] = id;
                return { id, ...data, ...updatedData } as T;
            },
            revalidate: false,
            throwOnError: false,
        });

        mutate(endpoint, updated, {
            optimisticData: (list?: Array<T>) => {
                if (!list) return [];
                const index = list.findIndex(
                    (item: T) => String(item[idKey]) === id,
                );
                if (index === -1) {
                    mutate(endpoint); // trigger revalidation
                    return list;
                }
                list.splice(index, 1, { ...list[index], ...updatedData });
                return list;
            },
            populateCache: (updated: T, list?: Array<T>) => {
                if (!list) return [];
                if (!updated) return list;
                const index = list.findIndex(
                    (item: T) => item[idKey] === updated[idKey],
                );
                if (index === -1) {
                    console.warn(
                        "swrcrud: update: updated element not found in list view",
                    );
                    mutate(endpoint); // trigger revalidation
                    return list;
                }
                list.splice(index, 1, updated);
                return list;
            },
            revalidate: false,
            throwOnError: false,
        });

        return updated;
    };

    const remove = async (id: idType) => {
        if (!id) return;
        const key = normalizeFinalSlash(endpoint) + id;
        const removed = await removeFetcher(key);
        mutate(endpoint, removed, {
            optimisticData: (list?: Array<T>) =>
                list
                    ? list.filter((item: T) => String(item[idKey]) !== id)
                    : [],
            populateCache: (_, list?: Array<T>) => {
                if (!list) return [];
                return list.filter((item: T) => item[idKey] !== id);
            },
            revalidate: false,
        });
        mutate(key, removed, {
            optimisticData: () => undefined,
            populateCache: () => undefined,
            revalidate: false,
        });

        return removed;
    };

    const createOrUpdate = (data: Partial<T>, id: any) => {
        if (!id) return;
        const updated: Partial<T> = { ...data };
        updated[idKey] = id;
        mutate(endpoint, createOrUpdateFetcher(endpoint, updated), {
            optimisticData: (list: Array<T> | undefined) => {
                if (!list) return [];
                const old = list.find((item: T) => item[idKey] === id) || {};
                const optimistic = {
                    ...createDefaultOptimisticData,
                    ...old,
                    ...updated,
                } as T;
                return [
                    ...list.filter((item: T) => item[idKey] !== id),
                    optimistic,
                ];
            },
            populateCache: (updated: T, list: Array<T> | undefined) => {
                if (!updated) return list || [];
                if (!list) return [updated];
                return [
                    ...list.filter((item: T) => item[idKey] !== id),
                    updated,
                ];
            },
            revalidate: true,
        });
    };

    return { create, copy, update, remove, createOrUpdate };
};
