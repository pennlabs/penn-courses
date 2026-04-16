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
    window.location.pathname + window.location.search
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

// To check that the course was offered as a certain code@semester,
// specify it with `checkOfferedIn`.
// Null will be returned if the course was not offered in that semester.
export function apiLive(code, checkOfferedIn) {
  return apiFetch(
    `${API_DOMAIN}/api/base/current/courses/${encodeURIComponent(code)}/` +
      (checkOfferedIn
        ? `?check_offered_in=${encodeURIComponent(checkOfferedIn)}`
        : "")
  );
}

function getSemesterQParam(semester) {
  return semester ? `&semester=${encodeURIComponent(semester)}` : "";
}

export function apiReviewData(type, code, semester) {
  return apiFetch(
    `${API_DOMAIN}/api/review/${encodeURIComponent(type)}/${encodeURIComponent(
      code
    )}?token=${encodeURIComponent(API_TOKEN)}` + getSemesterQParam(semester)
  );
}

export function apiContact(name) {
  return apiFetch(
    `https://api.pennlabs.org/directory/search?name=${encodeURIComponent(name)}`
  )
    .then(res => {
      if (res.result_data.length !== 1) {
        return null;
      }

      return {
        email: res.result_data[0].list_email,
        organization: res.result_data[0].list_organization,
        title: res.result_data[0].list_title_or_major
      };
    })
    .catch(error => {
      // TODO: refactor to avoid labs-api-server, currently not working
      return null;
    });
}

export function apiHistory(course, instructor, semester) {
  return apiFetch(
    `${API_DOMAIN}/api/review/course/${encodeURIComponent(
      course
    )}/${encodeURIComponent(instructor)}?token=${encodeURIComponent(
      API_TOKEN
    )}` + getSemesterQParam(semester)
  );
}

export function apiFetchPCADemandChartData(course, semester) {
  return apiFetch(
    `${API_DOMAIN}/api/review/course_plots/${encodeURIComponent(
      course
    )}?token=${encodeURIComponent(API_TOKEN)}` + getSemesterQParam(semester)
  );
}

//cache attributes data in browser memory
let uncompressedAttributesData = null;

export function apiAttributes() {
  // Instant return if fetched already in this session
  if (uncompressedAttributesData) {
    return Promise.resolve(uncompressedAttributesData);
  }

  const key = "meta-pcr-attributes";
  const cached_attributes_str = localStorage.getItem(key);
  
  // Helper function to format the data so we don't repeat code in the frontend
  const processAttributes = (data) => {
    return data.map(attr => attr.code).sort((a, b) => a.localeCompare(b));
  };

  if (cached_attributes_str) {
    // We have cached data
    let cached_attributes;
    try {
      cached_attributes = JSON.parse(cached_attributes_str);
    } catch (e) {
      localStorage.removeItem(key);
    }
    if (cached_attributes) {
      // Use a background fetch to update the cache silently
      apiFetch(`${API_DOMAIN}/api/base/attributes/`)
        .then(data => {
          const processedCodes = processAttributes(data);
          uncompressedAttributesData = processedCodes; // Update memory
          try {
            localStorage.setItem(key, JSON.stringify(processedCodes)); // Update storage
          } catch (e) {
            localStorage.removeItem(key);
          }
        })
        .catch(console.error); 

      // Instantly return the old cache
      uncompressedAttributesData = cached_attributes;
      return Promise.resolve(cached_attributes);
    }
  }

  // We have no cache, so set everything up
  return new Promise((resolve, reject) => {
    apiFetch(`${API_DOMAIN}/api/base/attributes/`)
      .then(data => {
        const processedCodes = processAttributes(data);
        uncompressedAttributesData = processedCodes; // Set memory
        
        try {
          localStorage.setItem(key, JSON.stringify(processedCodes)); // Set storage
        } catch (e) {
          localStorage.removeItem(key);
        }
        
        resolve(processedCodes);
      })
      .catch(reject);
  });
}

export function apiCourseSearch(semester, attributes, difficulty, course_quality, instructor_quality, days, time, departments, page = 1) {
  const url = `${API_DOMAIN}/api/base/${encodeURIComponent(semester)}/courses/?` +
      (attributes ? `attributes=${encodeURIComponent(attributes)}&` : "") +
      (difficulty ? `difficulty=${encodeURIComponent(difficulty)}&` : "") +
      (course_quality ? `course_quality=${encodeURIComponent(course_quality)}&` : "") +
      (instructor_quality ? `instructor_quality=${encodeURIComponent(instructor_quality)}&` : "") +
      (days ? `days=${encodeURIComponent(days)}&` : "") +
      (time ? `time=${encodeURIComponent(time)}&` : "") +
      (departments ? `departments=${encodeURIComponent(departments)}&` : "") +
      `page=${page}`;
  console.log(url);
  return apiFetch(url);
}