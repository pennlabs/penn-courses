import React from "react";
import styled from "@emotion/styled";
import Modal from "pcx-shared-components/src/common/modal";
import { Center } from "pcx-shared-components/src/common/layout";

const ButtonRow = styled.div`
  display: flex;
  justify-content: center;
  margin-top: 1rem;
`;

const LogoutButton = styled.button`
  display: inline-flex;
  align-items: center;
  height: 2.25rem;
  padding: 0 1rem;
  font-size: 0.85rem;
  color: #fff;
  background-color: #3273dc;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  &:hover {
    background-color: #276cda;
  }
  &:active {
    background-color: #2366d1;
  }
`;

interface NoAccessModalProps {
  onLogout: () => void;
}

const NoAccessModal = ({ onLogout }: NoAccessModalProps) => (
  <Modal title="No access">
    <Center>
      Your account doesn&apos;t have access to Penn Degree Plan yet. Stay tuned for the beta!
    </Center>
    <ButtonRow>
      <LogoutButton
        type="button"
        onClick={() =>
          fetch("/accounts/logout/", { method: "GET", redirect: "follow" })
            .catch(() => undefined)
            .then(onLogout)
        }
      >
        Logout
      </LogoutButton>
    </ButtonRow>
  </Modal>
);

export default NoAccessModal;
