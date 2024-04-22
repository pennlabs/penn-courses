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

export function apiComments(code) {
  if(code === "CIS-1200") {
    return Promise.resolve({
      comments: [
        {
          title: "Hi 1",
          content: "I love this course :)",
          id: 10,
          created_at: new Date(),
          modified_at: new Date(),
          author_name: "Luke Tong",
          likes: 69,
          course: "CIS-1200",
          semester: "2024A",
          parent_id: null,
          path: "10",
        },
        {
          title: "Hi 2",
          content: "Luke is so cool and awesome",
          id: 11,
          created_at: new Date(new Date() - 10),
          modified_at: new Date(new Date() - 10),
          author_name: "Penn Labs",
          likes: 100,
          course: "CIS-1200",
          semester: "2024A",
          parent_id: 10,
          path: "10.11",
        },
        {
          title: "Hi 3",
          content: "I hate this course :(",
          id: 20,
          created_at: new Date(new Date() - 10),
          modified_at: new Date(new Date() - 10),
          author_name: "Shiva Mehta",
          likes: 0,
          course: "CIS-1200",
          semester: "2022A",
          parent_id: null,
          path: "20",
        },
        {
          title: "Hi 4",
          content: "I TA this course :|",
          id: 30,
          created_at: new Date(new Date() - 5),
          modified_at: new Date(new Date() - 5),
          author_name: "Eunsoo Shin",
          likes: 10,
          course: "CIS-1200",
          semester: "2022A",
          parent_id: null,
          path: "30",
        },
      ],
    });
  } else {
    return Promise.resolve({
      comments: [],
    })
  }
  
  /*
  return apiFetch(
    `${API_DOMAIN}/api/review/${encodeURIComponent(type)}/${encodeURIComponent(
      code
    )}/comments?token=${encodeURIComponent(API_TOKEN)}` + getSemesterQParam(semester)
  );
  */
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
