import autocompleteWorker from "workerize-loader!../workers/autocomplete.worker"; // eslint-disable-line import/no-webpack-loader-syntax

const autocompleteWorkerInstance = autocompleteWorker();
const compressAutocomplete = autocompleteWorkerInstance.compress;
const decompressAutocomplete = autocompleteWorkerInstance.decompress;

const API_DOMAIN = `${window.location.protocol}//${window.location.host}`;
const PUBLIC_API_TOKEN = "public";
const API_TOKEN = "platform";

function apiFetch(url) {
  return fetch(url).then(res => res.json());
}

export function redirectForAuth() {
  window.location.href = `${API_DOMAIN}/accounts/login/?next=${encodeURIComponent(
    window.location.pathname
  )}`;
}

export function getLogoutUrl() {
  return `${API_DOMAIN}/accounts/logout/?next=${encodeURIComponent(
    `${window.location.origin}/logout`
  )}`;
}

// Necessary for backwards compatibility (we used to just store uncompressed
// JSON stringified autocomplete data)
const isCompressedAutocomplete = data => {
  return data.startsWith("compressed:");
};

// Cache the decompressed autocomplete dump as a global variable
var uncompressedAutocompleteData = null;

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

export async function apiCheckAuth() {
  const res = await fetch(`${API_DOMAIN}/accounts/me/`);
  if (res.status < 300 && res.status >= 200) {
    return true;
  } else {
    return false;
  }
}

export function apiIsAuthenticated(func) {
  apiFetch(
    `${API_DOMAIN}/api/review/auth?token=${encodeURIComponent(
      PUBLIC_API_TOKEN
    )}`
  ).then(data => {
    if (data.authed == null) {
      window.Raven.captureMessage(`Auth check error: ${JSON.stringify(data)}`, {
        level: "error"
      });
    }
    func(data.authed);
  });
}

export function apiLive(code) {
  return apiFetch(
    `${API_DOMAIN}/api/base/current/courses/${encodeURIComponent(code)}/`
  );
}

export function apiReviewData(type, code) {
  return apiFetch(
    `${API_DOMAIN}/api/review/${encodeURIComponent(type)}/${encodeURIComponent(
      code
    )}?token=${encodeURIComponent(API_TOKEN)}`
  );
}

export function apiContact(name) {
  return apiFetch(
    `https://api.pennlabs.org/directory/search?name=${encodeURIComponent(name)}`
  ).then(res => {
    if (res.result_data.length !== 1) {
      return null;
    }

    return {
      email: res.result_data[0].list_email,
      organization: res.result_data[0].list_organization,
      title: res.result_data[0].list_title_or_major
    };
  });
}

export function apiHistory(course, instructor) {
  return apiFetch(
    `${API_DOMAIN}/api/review/course/${encodeURIComponent(
      course
    )}/${encodeURIComponent(instructor)}?token=${encodeURIComponent(API_TOKEN)}`
  );
}

export function apiFetchPCADemandChartData(course) {
  return apiFetch(
    `${API_DOMAIN}/api/review/course_plots/${encodeURIComponent(
      course
    )}?token=${encodeURIComponent(API_TOKEN)}`
  );
}
