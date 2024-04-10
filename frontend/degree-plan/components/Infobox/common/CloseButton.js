import styled from "@emotion/styled";
import React from "react";
import { GrayIcon } from "../../common/bulma_derived_components";

const CloseIcon = styled(GrayIcon)`
  pointer-events: auto;
  margin-left: 0.5rem;

  & :hover {
    color: #707070;
  }
`;

const CloseButton = ({ close }) => (
  <CloseIcon onClick={close}>
    <i className="fas fa-times fa-md" />
  </CloseIcon>
);

export default CloseButton;
