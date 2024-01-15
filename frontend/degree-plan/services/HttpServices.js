import axios from "axios";
// import { toast } from "react-toastify";
// https://meh-server.herokuapp.com
export const baseURL = "http://localhost:8000/api";

axios.defaults.baseURL = baseURL;
axios.defaults.headers.post['Access-Control-Allow-Origin'] = '*';
// axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
// axios.defaults.xsrfCookieName = "platform";
// axios.defaults.withCredentials = true;

axios.interceptors.response.use(null, (e) => {
  const expectedError =
    e.response && e.response.status >= 400 && e.response.status < 500;
  if (!expectedError) {
    console.log("logging the error", e);
    // toast.error("an unexpected error occured...");
  }
  return Promise.reject(e);
});

export default {
  get: axios.get,
  post: axios.post,
  put: axios.put,
  delete: axios.delete,
};
