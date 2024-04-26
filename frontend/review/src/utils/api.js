import autocompleteWorker from "workerize-loader!../workers/autocomplete.worker"; // eslint-disable-line import/no-webpack-loader-syntax
import getCsrf from "./csrf";

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

export function apiComments(course, semester, professorId, sortBy) {
  console.log("fetching comments");
  if(!semester && !professorId && !sortBy) {
    return Promise.resolve({ ...fakeComments, ...fakeSemesters})
  }
  return Promise.resolve({ comments: fakeComments.comments.filter((comment) => {
    return (course == null || comment.course === course) && 
    (semester == null || comment.semester === semester) && 
    (professorId == null || comment.professorId === professorId)
  })})

  /*
  return apiFetch(
    `${API_DOMAIN}/api/review/${encodeURIComponent(type)}/${encodeURIComponent(
      code
    )}/comments?token=${encodeURIComponent(API_TOKEN)}` + getSemesterQParam(semester)
  );
  */
}

export function apiReplies(commentId) {
  console.log("fetching replies");
  return Promise.resolve({ replies: fakeReplies.replies.filter(reply => reply.parent_id === commentId)} );
}

export function apiPostComment(course, semester, content) {
  return apiFetch(
    `${API_DOMAIN}/api/review/comment`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrf(),
      },
      body: JSON.stringify({
        text: content,
        course_code: "CIS-1600",
        instructor: [130],
        semester: semester,
      })
    }
  );
}

export function apiUserComment(course) {
  console.log("fetching user comment");
  return Promise.resolve({});
  if(course === "CIS-120") return Promise.resolve(fakeUserComment);
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
