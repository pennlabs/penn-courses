const API_DOMAIN = `${window.location.protocol}//${window.location.host}`;
const API_TOKEN = "platform";

export const queryKeys = {
  checkAuth: ["checkAuth"],
  autocomplete: ["autocomplete"],
  attributes: ["attributes"],
  courseSearch: params => ["courseSearch", params],
  reviewData: (type, code, semester) => ["reviewData", type, code, semester],
  live: (code, checkOfferedIn) => ["live", code, checkOfferedIn],
  history: (course, instructor, semester) => [
    "history",
    course,
    instructor,
    semester
  ],
  pcaChartData: (course, semester) => ["pcaChartData", course, semester],
  contact: name => ["contact", name]
};

async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request to ${url} failed with status ${res.status}`);
  }
  return res.json();
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

export function apiAutocomplete() {
  return apiFetch(`${API_DOMAIN}/api/review/autocomplete`);
}

export async function apiCheckAuth() {
  const res = await fetch(`${API_DOMAIN}/accounts/me/`);
  if (res.status < 300 && res.status >= 200) {
    return true;
  } else {
    return false;
  }
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

export function apiAttributes() {
  return apiFetch(`${API_DOMAIN}/api/base/attributes/`).then(data =>
    data.map(attr => attr.code).sort((a, b) => a.localeCompare(b))
  );
}

export function apiCourseSearch(params, page = 1) {
  const {
    semester,
    attributes,
    difficulty,
    course_quality,
    instructor_quality,
    days,
    time,
    departments
  } = params;
  const url =
    `${API_DOMAIN}/api/base/${encodeURIComponent(semester)}/courses/?` +
    (attributes ? `attributes=${encodeURIComponent(attributes)}&` : "") +
    (difficulty ? `difficulty=${encodeURIComponent(difficulty)}&` : "") +
    (course_quality
      ? `course_quality=${encodeURIComponent(course_quality)}&`
      : "") +
    (instructor_quality
      ? `instructor_quality=${encodeURIComponent(instructor_quality)}&`
      : "") +
    (days ? `days=${encodeURIComponent(days)}&` : "") +
    (time ? `time=${encodeURIComponent(time)}&` : "") +
    (departments ? `departments=${encodeURIComponent(departments)}&` : "") +
    `page=${page}`;
  return apiFetch(url);
}
