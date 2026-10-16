import { QueryClient } from "@tanstack/react-query";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";
import autocompleteWorker from "workerize-loader!../workers/autocomplete.worker"; // eslint-disable-line import/no-webpack-loader-syntax
import { queryKeys } from "./api";

const autocompleteWorkerInstance = autocompleteWorker();
const compressAutocomplete = autocompleteWorkerInstance.compress;
const decompressAutocomplete = autocompleteWorkerInstance.decompress;

// Prefixed "meta-" so the course cart's getCartCourses() (which treats
// every non-"meta-" localStorage key as a cart item) ignores this entry.
const PERSIST_STORAGE_KEY = "meta-pcr-query-cache";

// The autocomplete/attributes dumps are large, rarely change
const STATIC_QUERY_OPTIONS = {
  staleTime: 1000 * 60 * 60, // 1 hour
  gcTime: 1000 * 60 * 60 * 24 // 24 hours
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      networkMode: "always"
    }
  }
});

queryClient.setQueryDefaults(queryKeys.autocomplete, STATIC_QUERY_OPTIONS);
queryClient.setQueryDefaults(queryKeys.attributes, STATIC_QUERY_OPTIONS);

export const asyncStoragePersister = createAsyncStoragePersister({
  key: PERSIST_STORAGE_KEY,

  serialize: data => data,
  deserialize: data => data,
  storage: {
    getItem: async key => {
      const cached = localStorage.getItem(key);
      if (!cached) return null;
      try {
        return await decompressAutocomplete(cached);
      } catch (e) {
        localStorage.removeItem(key);
        return null;
      }
    },
    setItem: async (key, value) => {
      try {
        const compressed = await compressAutocomplete(value);
        localStorage.setItem(key, compressed);
      } catch (e) {
        localStorage.removeItem(key);
      }
    },
    removeItem: key => localStorage.removeItem(key)
  }
});

export const persistOptions = {
  persister: asyncStoragePersister,
  maxAge: 1000 * 60 * 60 * 24 * 7, // 1 week
  dehydrateOptions: {
    // Only autocomplete/attributes are large + slow-changing enough to be
    // worth persisting to localStorage
    shouldDehydrateQuery: query => {
      const [rootKey] = query.queryKey;
      return (
        query.state.status === "success" &&
        (rootKey === queryKeys.autocomplete[0] ||
          rootKey === queryKeys.attributes[0])
      );
    }
  }
};
