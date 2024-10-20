import { PropsWithChildren } from "react";
import { GrayIcon } from "@/components/common/bulma_derived_components";

interface ErrorBoxProps {
    detail?: string;
}

export const ErrorBox = ({ children, detail }: PropsWithChildren<ErrorBoxProps>) => (
  <div style={{ textAlign: "center", padding: 45 }}>
    <i
      className="fa fa-exclamation-circle"
      style={{ fontSize: "5rem", color: "#aaa" }}
    />
    <h1 style={{ fontSize: "1.25em", marginTop: 15 }}>{children}</h1>
    <small>
      {detail} If you think this is an error, contact Penn Labs at{" "}
      <a href="mailto:contact@pennlabs.org">contact@pennlabs.org</a>.
    </small>
  </div>
);