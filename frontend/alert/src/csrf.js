/**
 * @returns {string | boolean} The CSRF token used by the Django REST Framework
 */
const getCsrf = () => {
    const result =
        document.cookie &&
        document.cookie
            .split("; ")
            .reduce(
                (acc, cookie) =>
                    acc ||
                    (cookie.substring(0, "csrftoken".length + 1) ===
                        "csrftoken=" &&
                        decodeURIComponent(
                            cookie.substring("csrftoken=".length)
                        )),
                null
            );
    return result;
};

export default getCsrf;
