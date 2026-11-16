import React, { useEffect, useState } from "react";
import styled from "@emotion/styled";
import Modal from "pcx-shared-components/src/common/modal";
import { Center } from "pcx-shared-components/src/common/layout";
import { getFetcher, postFetcher } from "@/hooks/swrcrud";

const BETA_ACCESS_URL = "/api/degree/beta-access";

type BetaStatus = "NONE" | "REQUESTED" | "APPROVED" | "DENIED";

const ButtonRow = styled.div`
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const Button = styled.button<{ $primary?: boolean }>`
  display: inline-flex;
  align-items: center;
  height: 2.25rem;
  padding: 0 1rem;
  font-size: 0.85rem;
  color: ${(props) => (props.$primary ? "#fff" : "#3273dc")};
  background-color: ${(props) => (props.$primary ? "#3273dc" : "#fff")};
  border: 1px solid #3273dc;
  border-radius: 4px;
  cursor: pointer;
  &:hover {
    background-color: ${(props) => (props.$primary ? "#276cda" : "#f2f6fd")};
  }
  &:disabled {
    opacity: 0.6;
    cursor: default;
  }
`;

const ErrorText = styled.div`
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: #c0392b;
  text-align: center;
`;

const MESSAGES: Record<BetaStatus, string> = {
  NONE: "Your account doesn't have access to Penn Degree Plan yet. Request access to join the beta!",
  REQUESTED: "Thanks! Your request to join the beta is in, and we'll let you in as soon as we can.",
  APPROVED: "You're in the beta! Reload the page to get started.",
  DENIED: "Your request to join the beta wasn't approved this time.",
};

interface NoAccessModalProps {
  onLogout: () => void;
}

const NoAccessModal = ({ onLogout }: NoAccessModalProps) => {
  const [status, setStatus] = useState<BetaStatus>("NONE");
  const [sending, setSending] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    getFetcher(BETA_ACCESS_URL)
      .then((data: { status: BetaStatus }) => setStatus(data.status))
      .catch(() => undefined);
  }, []);

  const requestAccess = () => {
    setSending(true);
    setFailed(false);
    postFetcher(BETA_ACCESS_URL)
      .then((data: { status: BetaStatus }) => setStatus(data.status))
      .catch(() => setFailed(true))
      .finally(() => setSending(false));
  };

  const logout = () =>
    fetch("/accounts/logout/", { method: "GET", redirect: "follow" })
      .catch(() => undefined)
      .then(onLogout);

  return (
    <Modal title="No access">
      <Center>{MESSAGES[status]}</Center>
      {failed && <ErrorText>Couldn&apos;t send your request. Please try again.</ErrorText>}
      <ButtonRow>
        {status === "NONE" && (
          <Button type="button" $primary disabled={sending} onClick={requestAccess}>
            {sending ? "Requesting…" : "Request beta access"}
          </Button>
        )}
        {status === "APPROVED" && (
          <Button type="button" $primary onClick={() => window.location.reload()}>
            Reload
          </Button>
        )}
        <Button type="button" onClick={logout}>
          Logout
        </Button>
      </ButtonRow>
    </Modal>
  );
};

export default NoAccessModal;
