import React from "react";
import withLayout from "../constants/withLayout";
import { ErrorBox } from "../components/common";

const ErrorPage = () => withLayout(<ErrorBox>404 Page Not Found</ErrorBox>);

export default ErrorPage;
