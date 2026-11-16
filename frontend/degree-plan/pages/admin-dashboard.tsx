import React, { useCallback, useState } from "react";
import Head from "next/head";
import Link from "next/link";
import styled from "@emotion/styled";
import useSWR from "swr";
import TopBar from "@/components/TopBar";
import {
  PanelContainer,
  PanelHeader,
  PanelTopBarButton,
} from "@/components/FourYearPlan/PanelCommon";
import { getFetcher, patchFetcher, postFetcher } from "@/hooks/swrcrud";
import { User } from "@/types";

const REQUESTS_URL = "/api/degree/beta-requests";

type Status = "REQUESTED" | "APPROVED" | "DENIED";

interface BetaRequest {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  status: Status;
  created_at: string;
  decided_at: string | null;
}

const FILTERS: { label: string; status: Status | null }[] = [
  { label: "Pending", status: "REQUESTED" },
  { label: "Approved", status: "APPROVED" },
  { label: "Denied", status: "DENIED" },
  { label: "All", status: null },
];

const STATUS_LABELS: Record<Status, string> = {
  REQUESTED: "Pending",
  APPROVED: "Approved",
  DENIED: "Denied",
};

const PageContainer = styled.div`
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
`;

const Body = styled.div`
  flex-grow: 1;
  background-color: var(--background-light-grey);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: center;

  @media (max-width: 767px) {
    padding: 1rem;
  }
`;

const Section = styled(PanelContainer)`
  max-width: 64rem;
  height: auto;
  overflow: hidden;
`;

const BackLink = styled(PanelTopBarButton)`
  background: transparent;
  text-decoration: none;
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 700;
`;

const SectionBody = styled.div`
  padding: 1rem 1.25rem 1.25rem;
`;

const Toolbar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
`;

const Tabs = styled.div`
  display: flex;
  gap: 0.25rem;
`;

const Tab = styled.button<{ $active: boolean }>`
  padding: 0.35rem 0.6rem;
  border: none;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  background: ${(props) => (props.$active ? "var(--primary-color-light)" : "transparent")};
  color: ${(props) =>
    props.$active ? "var(--primary-color-xxx-dark)" : "var(--primary-color-ultra-dark)"};

  &:hover {
    background: var(--primary-color-light);
  }
`;

const GrantForm = styled.form`
  display: flex;
  gap: 0.5rem;

  input {
    font: inherit;
    font-size: 0.9rem;
    padding: 0.4rem 0.75rem;
    border: none;
    border-radius: 0.75rem;
    background-color: var(--background-grey);
    color: black;
    outline: none;
    min-width: 0;
  }
`;

const Button = styled.button<{ $tone?: "approve" | "deny" }>`
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.35rem 0.8rem;
  border-radius: 5px;
  cursor: pointer;
  white-space: nowrap;
  border: none;
  color: ${(props) => (props.$tone === "deny" ? "var(--error-color)" : "#fff")};
  background: ${(props) =>
    props.$tone === "deny" ? "rgba(169, 68, 66, 0.08)" : "var(--modal-button-color)"};

  &:hover {
    background: ${(props) =>
      props.$tone === "deny" ? "rgba(169, 68, 66, 0.15)" : "var(--primary-color-xxx-dark)"};
  }
  &:disabled {
    opacity: 0.5;
    cursor: default;
  }
`;

const Rows = styled.ul`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Row = styled.li`
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1.6fr) auto auto;
  align-items: center;
  gap: 1rem;
  padding: 0.65rem 0.9rem;
  border-radius: 9px;
  background-color: var(--background-grey);
  box-shadow: rgba(0, 0, 0, 0.04) 0px 0px 0px 1px;

  @media (max-width: 767px) {
    grid-template-columns: minmax(0, 1fr) auto;
    .wide {
      display: none;
    }
  }
`;

const Person = styled.div`
  min-width: 0;
  div:first-of-type {
    font-weight: 600;
    color: var(--primary-color-ultra-dark);
  }
  div + div {
    font-size: 0.8rem;
    color: var(--text-color);
  }
`;

const Meta = styled.div`
  min-width: 0;
  font-size: 0.85rem;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const Badge = styled.span<{ $status: Status }>`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  color: ${({ $status }) =>
    $status === "APPROVED"
      ? "var(--green-color)"
      : $status === "DENIED"
      ? "var(--error-color)"
      : "var(--warning-text)"};
  background: ${({ $status }) =>
    $status === "APPROVED" ? "#E6F4EA" : $status === "DENIED" ? "#fbeaea" : "var(--warning-bg)"};
`;

const Actions = styled.div`
  display: flex;
  gap: 0.4rem;
  justify-content: flex-end;
`;

const Note = styled.p`
  color: var(--text-color);
  padding: 2rem 0;
  text-align: center;
`;

const ErrorText = styled.p`
  color: var(--error-color);
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
`;

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });

const errorMessage = (error: any) => {
  const info = error?.info;
  if (info?.username) return [].concat(info.username).join(" ");
  return info?.detail ?? "Something went wrong. Please try again.";
};

const BetaRequests = () => {
  const [filter, setFilter] = useState<Status | null>("REQUESTED");
  const [pennkey, setPennkey] = useState("");
  const [busyId, setBusyId] = useState<number | "grant" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const key = `${REQUESTS_URL}${filter ? `?status=${filter}` : ""}`;
  const { data: requests, error, mutate } = useSWR<BetaRequest[]>(key, getFetcher);

  const run = async (id: number | "grant", action: () => Promise<unknown>) => {
    setBusyId(id);
    setActionError(null);
    try {
      await action();
      await mutate();
      return true;
    } catch (e) {
      setActionError(errorMessage(e));
      return false;
    } finally {
      setBusyId(null);
    }
  };

  const decide = (request: BetaRequest, status: Status) =>
    run(request.id, () => patchFetcher(`${REQUESTS_URL}/${request.id}`, { status }));

  const grant = (e: React.FormEvent) => {
    e.preventDefault();
    const username = pennkey.trim();
    if (!username) return;
    run("grant", () => postFetcher(REQUESTS_URL, { username })).then((ok) => ok && setPennkey(""));
  };

  let list: React.ReactNode;
  if (error) list = <Note>{errorMessage(error)}</Note>;
  else if (!requests) list = <Note>Loading…</Note>;
  else if (!requests.length)
    list = <Note>{filter === "REQUESTED" ? "No pending requests." : "Nobody here yet."}</Note>;
  else
    list = (
      <Rows>
        {requests.map((request) => (
          <Row key={request.id}>
            <Person>
              <div>{`${request.first_name} ${request.last_name}`.trim() || request.username}</div>
              <div>{request.username}</div>
            </Person>
            <Meta className="wide" title={request.email}>
              {request.email || "No email"} · requested {formatDate(request.created_at)}
            </Meta>
            <Badge className="wide" $status={request.status}>
              {STATUS_LABELS[request.status]}
            </Badge>
            <Actions>
              {request.status !== "APPROVED" && (
                <Button
                  type="button"
                  disabled={busyId === request.id}
                  onClick={() => decide(request, "APPROVED")}
                >
                  Approve
                </Button>
              )}
              {request.status !== "DENIED" && (
                <Button
                  type="button"
                  $tone="deny"
                  disabled={busyId === request.id}
                  onClick={() => decide(request, "DENIED")}
                >
                  {request.status === "APPROVED" ? "Revoke" : "Deny"}
                </Button>
              )}
            </Actions>
          </Row>
        ))}
      </Rows>
    );

  return (
    <Section>
      <PanelHeader>
        <SectionTitle>Beta requests</SectionTitle>
        <Link href="/" passHref legacyBehavior>
          <BackLink as="a">
            <i className="fas fa-arrow-left" aria-hidden />
            Back to plan
          </BackLink>
        </Link>
      </PanelHeader>
      <SectionBody>
        <Toolbar>
          <Tabs role="tablist" aria-label="Filter by status">
            {FILTERS.map(({ label, status }) => (
              <Tab
                key={label}
                type="button"
                role="tab"
                aria-selected={filter === status}
                $active={filter === status}
                onClick={() => setFilter(status)}
              >
                {label}
              </Tab>
            ))}
          </Tabs>
          <GrantForm onSubmit={grant}>
            <input
              aria-label="PennKey to grant access"
              placeholder="PennKey"
              value={pennkey}
              onChange={(e) => setPennkey(e.target.value)}
            />
            <Button type="submit" disabled={busyId === "grant" || !pennkey.trim()}>
              Grant access
            </Button>
          </GrantForm>
        </Toolbar>
        {actionError && <ErrorText>{actionError}</ErrorText>}
        {list}
      </SectionBody>
    </Section>
  );
};

const AdminDashboardPage = () => {
  const { data: user, error: userError, isLoading, mutate } = useSWR<User>(
    "/accounts/me/",
    getFetcher,
    { shouldRetryOnError: false }
  );
  const setUser = useCallback((next: User | null) => mutate(next ?? undefined, false), [mutate]);
  const signedIn = !!user && !userError;

  let content: React.ReactNode;
  if (isLoading) content = <Note>Loading…</Note>;
  else if (!signedIn) content = <Note>Log in to Penn Degree Plan to use the admin dashboard.</Note>;
  else if (!user.is_staff) content = <Note>The admin dashboard is only for Penn Labs staff.</Note>;
  else content = <BetaRequests />;

  return (
    <PageContainer>
      <Head>
        <title>Admin dashboard · Penn Degree Plan</title>
      </Head>
      <TopBar
        user={signedIn ? user : null}
        login={setUser}
        logout={() => setUser(null)}
        planOpen
        setPlanOpen={() => {}}
        requirementsOpen
        setRequirementsOpen={() => {}}
        showColumnToggles={false}
      />
      <Body>{content}</Body>
    </PageContainer>
  );
};

export default AdminDashboardPage;
