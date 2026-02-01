/**
 * Polyfill for Promise.withResolvers if it's not available.
 */

export type PromiseWithResolvers<T> = {
    promise: Promise<T>;
    resolve: (value: T | PromiseLike<T>) => void;
    reject: (reason?: any) => void;
};

// Augment the global PromiseConstructor type
declare global {
    interface PromiseConstructor {
        withResolvers<T>(): PromiseWithResolvers<T>;
    }
}

export function polyfillPromiseWithResolvers() {
    if (typeof Promise.withResolvers !== "function") {
        Object.defineProperty(Promise, "withResolvers", {
            value: function <T>(): PromiseWithResolvers<T> {
                let resolve!: (value: T | PromiseLike<T>) => void;
                let reject!: (reason?: any) => void;

                const promise = new Promise<T>((res, rej) => {
                    resolve = res;
                    reject = rej;
                });

                return { promise, resolve, reject };
            },
            writable: true,
            configurable: true,
        });
    }
}

export default function PolyfillWithResolver() {
    return;
}
