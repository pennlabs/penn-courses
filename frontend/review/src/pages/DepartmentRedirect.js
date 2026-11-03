import { useEffect } from "react";
import { useFilterDispatch } from "../utils/FilterContext";
import { filtersForDepartment, getFilteredURL } from "../utils/filters";

/**
 * Department pages were replaced by the browse page's department filter, so old
 * /department/:code links open the browse page filtered to that department.
 */
const DepartmentRedirect = ({ match, history }) => {
  const dispatch = useFilterDispatch();
  const { code } = match.params;

  useEffect(() => {
    const filters = filtersForDepartment(code);
    dispatch({ type: "SET_ALL", payload: filters });
    // Replace so Back skips the old URL instead of redirecting again
    history.replace(getFilteredURL(filters));
  }, [code, dispatch, history]);

  return null;
};

export default DepartmentRedirect;
