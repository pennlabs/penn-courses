/**
 * Polyfill for Promise.withResolvers if it's not available.
 */
 
export type PromiseWithResolvers<T> = {
    promise: Promise<T>;
    resolve: (value: T | PromiseLike<T>) => void;
    reject: (reason?: any) => void;
  };
  
  export function polyfillPromiseWithResolvers() {
    if (!Promise.withResolvers) {
      Promise.withResolvers = function <T>(): PromiseWithResolvers<T> {
        let resolve: (value: T | PromiseLike<T>) => void;
        let reject: (reason?: any) => void;
  
        const promise = new Promise<T>((res, rej) => {
          resolve = res;
          reject = rej;
        });
  
        return { promise, resolve: resolve!, reject: reject! };
      };
    }
  }