/**
 * @returns {string | boolean} The CSRF token used by the Django REST Framework
 */
const getCsrf = (): string | boolean => {
    const result =
        document.cookie &&
        document.cookie
            .split("; ")
            .reduce(
                (acc: string | boolean, cookie) =>
                    acc ||
                    (cookie.substring(0, "csrftoken".length + 1) ===
                        "csrftoken=" &&
                        decodeURIComponent(
                            cookie.substring("csrftoken=".length)
                        )),
                false
            );
    return result;
};

export default getCsrf;
