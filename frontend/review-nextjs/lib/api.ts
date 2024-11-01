import autocompleteWorker from "workerize-loader!../workers/autocomplete.worker"; // eslint-disable-line import/no-webpack-loader-syntax
const autocompleteWorkerInstance = autocompleteWorker();
const compressAutocomplete = autocompleteWorkerInstance.compress;
const decompressAutocomplete = autocompleteWorkerInstance.decompress;

const API_DOMAIN = `${window.location.protocol}//${window.location.host}`;
const PUBLIC_API_TOKEN = "public";
const API_TOKEN = "platform";

function apiFetch(url: string): Promise<any> {
  return fetch(url).then(res => res.json());
}

export const doAPIRequest = (path: string, options = {}): Promise<Response> =>
  fetch(`/api${path}`, options);

export function getLogoutUrl(): string {
  return `/accounts/logout/?next=${encodeURIComponent(
    `${window.location.origin}/logout`
  )}`;
}

export function redirectForAuth(): void {
  window.location.href = `/accounts/login/?next=${encodeURIComponent(
    window.location.pathname
  )}`;
}

export async function apiCheckAuth(): Promise<boolean> {
  const res = await doAPIRequest("/accounts/me/");
  if (res.status < 300 && res.status >= 200) {
    return true;
  } else {
    return false;
  }
}

const isCompressedAutocomplete = (data : string) : boolean => {
  return data.startsWith("compressed:");
};

// Cache the decompressed autocomplete dump as a global variable
let uncompressedAutocompleteData : string | null = null;

export function apiAutocomplete() {
  // If we have decompressed autocomplete data since last page refresh, return previous data.
  if (uncompressedAutocompleteData) {
    return Promise.resolve(uncompressedAutocompleteData);
  }
  // Cache the autocomplete JSON in local storage using the stale-while-revalidate
  // strategy.
  const key = "meta-pcr-autocomplete";
  const cached_autocomplete = localStorage.getItem(key);
  if (cached_autocomplete) {
    // If a cached version exists, replace it in the cache asynchronously and return the old cache.
    apiFetch(`${API_DOMAIN}/api/review/autocomplete`)
      .then(compressAutocomplete)
      .then(compressed => {
        try {
          localStorage.setItem(key, compressed);
        } catch (e) {
          localStorage.removeItem(key);
        }
      });
    return isCompressedAutocomplete(cached_autocomplete)
      ? decompressAutocomplete(cached_autocomplete)
      : Promise.resolve(cached_autocomplete);
  } else {
    // If no cached data exists, fetch, set the cache and return in the same promise.
    return new Promise((resolve, reject) => {
      apiFetch(`${API_DOMAIN}/api/review/autocomplete`)
        .then(data => {
          resolve(data);
          return compressAutocomplete(data);
        })
        .then(compressed => {
          try {
            localStorage.setItem(key, compressed);
          } catch (e) {
            localStorage.removeItem(key);
          }
        });
    });
  }
}
