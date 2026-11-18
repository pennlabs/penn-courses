import React, { useEffect, useRef, useState } from "react";
import styled from "@emotion/styled";
import { keyframes } from "@emotion/react";
import useSWR from "swr";
import { getFetcher, postFetcher } from "@/hooks/swrcrud";
import Dialog, {
  DialogButton as Button,
  DialogButtons as Buttons,
  DialogContent as Content,
  DialogSubtitle as Subtitle,
  DialogTitle as Title,
} from "./common/Dialog";

const INVITES_URL = "/api/degree/beta-invites";
const MAX_FRIENDS = 3;

type InviteStatus = "PENDING" | "APPROVED" | "DENIED";

interface Invites {
  invites: { pennkey: string; status: InviteStatus; created_at: string }[];
  remaining: number;
}

// The program chip colors, so each friend gets their own.
const SEAT_COLORS = [
  {
    bg: "var(--program-degree-bg)",
    fg: "var(--program-degree)",
    border: "var(--program-degree-border)",
  },
  {
    bg: "var(--program-major-bg)",
    fg: "var(--program-major)",
    border: "var(--program-major-border)",
  },
  {
    bg: "var(--program-minor-bg)",
    fg: "var(--program-minor)",
    border: "var(--program-minor-border)",
  },
];

const pop = keyframes`
  0% { transform: scale(0.6); }
  60% { transform: scale(1.12); }
  100% { transform: scale(1); }
`;

const Seats = styled.div`
  display: flex;
  justify-content: center;
  gap: 0.9rem;
  margin-bottom: 1.25rem;
`;

const Seat = styled.div<{ $color: typeof SEAT_COLORS[number] | null }>`
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3.1rem;
  height: 3.1rem;
  border-radius: 50%;
  font-size: 1.2rem;
  font-weight: 700;
  text-transform: uppercase;
  color: ${(props) =>
    props.$color ? props.$color.fg : "var(--primary-color-extra-dark)"};
  background: ${(props) => (props.$color ? props.$color.bg : "#fff")};
  border: 2px ${(props) => (props.$color ? "solid" : "dashed")}
    ${(props) =>
      props.$color ? props.$color.border : "var(--primary-color-dark)"};
  animation: ${(props) => (props.$color ? pop : "none")} 280ms ease-out;
  transition: background 150ms ease, border-color 150ms ease;

  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const StatusBadge = styled.span<{ $approved: boolean }>`
  position: absolute;
  right: -4px;
  bottom: -4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  border: 2px solid #fff;
  background: ${(props) =>
    props.$approved ? "var(--green-color)" : "var(--fall-color)"};
  color: #fff;
  font-size: 0.55rem;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
`;

const Field = styled.label<{ $color: typeof SEAT_COLORS[number] }>`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  height: 2.6rem;
  padding: 0 1rem;
  border-radius: 999px;
  background: var(--background-grey);
  border: 2px solid transparent;
  transition: border-color 150ms ease, background 150ms ease;
  cursor: text;

  &:focus-within {
    background: #fff;
    border-color: ${(props) => props.$color.border};
  }

  .dot {
    flex-shrink: 0;
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    background: ${(props) => props.$color.border};
  }

  input {
    flex: 1;
    min-width: 0;
    border: none;
    outline: none;
    background: transparent;
    font: inherit;
    font-size: 0.95rem;
    color: var(--primary-color-ultra-dark);
  }

  input::placeholder {
    color: var(--primary-color-extra-dark);
  }

  .suffix {
    flex-shrink: 0;
    font-size: 0.85rem;
    color: var(--primary-color-extra-dark);
  }
`;

const ErrorText = styled.p`
  margin: 0;
  font-size: 0.85rem;
  color: var(--error-color);
`;

const Chips = styled.div`
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.4rem;
  margin-bottom: 1rem;
`;

const Chip = styled.span<{ $color: typeof SEAT_COLORS[number] }>`
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  color: ${(props) => props.$color.fg};
  background: ${(props) => props.$color.bg};
`;

const errorMessage = (error: any) => {
  const friends = error?.info?.friends;
  if (friends) return [].concat(friends).join(" ");
  return error?.info?.detail ?? "Couldn't send your invites. Please try again.";
};

const sentence = (names: string[]) =>
  names.length < 3
    ? names.join(" and ")
    : `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;

const InviteFriendsModal = ({ close }: { close: () => void }) => {
  const { data, mutate } = useSWR<Invites>(INVITES_URL, getFetcher);
  const [friends, setFriends] = useState(["", "", ""]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justSent, setJustSent] = useState<string[] | null>(null);
  const firstInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (data?.remaining) firstInput.current?.focus();
  }, [data?.remaining]);

  const invites = data?.invites ?? [];
  const sent = invites.map((invite) => invite.pennkey);
  const remaining = data?.remaining ?? 0;
  const open = friends.slice(0, remaining);
  const entered = open.map((f) => f.trim()).filter(Boolean);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!entered.length) return;
    setSending(true);
    setError(null);
    postFetcher(INVITES_URL, { friends: entered })
      .then((next: Invites) => {
        mutate(next, false);
        setFriends(["", "", ""]);
        setJustSent(entered.map((f) => f.toLowerCase()));
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setSending(false));
  };

  // Sent friends first, then whoever is being typed, then empty chairs.
  const seats = Array.from({ length: MAX_FRIENDS }, (_, i) => {
    if (i < sent.length)
      return { letter: sent[i][0], status: invites[i].status };
    const typed = open[i - sent.length]?.trim();
    return { letter: typed ? typed[0] : null, status: null };
  });

  let body: React.ReactNode;
  if (!data) {
    body = <Subtitle>Loading…</Subtitle>;
  } else if (justSent) {
    body = (
      <>
        <Title>Seat saved!</Title>
        <Subtitle>
          We&apos;ll take a look and let {sentence(justSent)} in soon.
        </Subtitle>
        <Buttons>
          {!!remaining && (
            <Button type="button" $quiet onClick={() => setJustSent(null)}>
              Invite another
            </Button>
          )}
          <Button type="button" onClick={close}>
            Back to planning
          </Button>
        </Buttons>
      </>
    );
  } else if (!remaining) {
    body = (
      <>
        <Title>Your crew is complete</Title>
        <Subtitle>
          You&apos;ve invited all three friends. Thanks for spreading the word!
        </Subtitle>
        <Chips>
          {sent.map((pennkey, i) => (
            <Chip key={pennkey} $color={SEAT_COLORS[i]}>
              {pennkey}
            </Chip>
          ))}
        </Chips>
        <Buttons>
          <Button type="button" onClick={close}>
            Back to planning
          </Button>
        </Buttons>
      </>
    );
  } else {
    body = (
      <>
        <Title>Bring your study buddies</Title>
        <Subtitle>
          Planning is more fun together. Invite up to {remaining}
          {sent.length ? " more" : ""} friend{remaining === 1 ? "" : "s"} to the
          Penn Degree Plan beta.
        </Subtitle>
        <Seats aria-hidden>
          {seats.map((seat, i) => (
            // Keyed on the letter too, so a seat pops again when its friend changes.
            <Seat
              // eslint-disable-next-line react/no-array-index-key
              key={`${i}-${seat.letter ?? ""}`}
              $color={seat.letter ? SEAT_COLORS[i] : null}
            >
              {seat.letter ?? (
                <i
                  className="fas fa-user-plus"
                  style={{ fontSize: "0.9rem" }}
                />
              )}
              {seat.status && seat.status !== "DENIED" && (
                <StatusBadge
                  $approved={seat.status === "APPROVED"}
                  title={
                    seat.status === "APPROVED" ? "They're in!" : "Waiting on us"
                  }
                >
                  <i
                    className={
                      seat.status === "APPROVED"
                        ? "fas fa-check"
                        : "fas fa-clock"
                    }
                  />
                </StatusBadge>
              )}
            </Seat>
          ))}
        </Seats>
        <Form onSubmit={submit}>
          {open.map((friend, i) => (
            // A fixed set of fields that never reorder, so the position is a stable key.
            // eslint-disable-next-line react/no-array-index-key
            <Field key={i} $color={SEAT_COLORS[sent.length + i]}>
              <span className="dot" aria-hidden />
              <input
                ref={i === 0 ? firstInput : undefined}
                aria-label={`Friend ${sent.length + i + 1}'s PennKey`}
                placeholder="pennkey"
                autoComplete="off"
                autoCapitalize="none"
                spellCheck={false}
                maxLength={16}
                value={friend}
                onChange={(e) => {
                  const pennkey = e.target.value.replace(/[^a-z0-9]/gi, "");
                  setFriends(friends.map((f, j) => (j === i ? pennkey : f)));
                }}
              />
              <span className="suffix" aria-hidden>
                @upenn.edu
              </span>
            </Field>
          ))}
          {error && <ErrorText role="alert">{error}</ErrorText>}
          <Buttons>
            <Button type="button" $quiet onClick={close}>
              Maybe later
            </Button>
            <Button type="submit" disabled={sending || !entered.length}>
              <i className="fas fa-paper-plane" aria-hidden />
              {sending ? "Sending…" : "Send invites"}
            </Button>
          </Buttons>
        </Form>
      </>
    );
  }

  return (
    <Dialog close={close} label="Invite friends to Penn Degree Plan">
      <Content>{body}</Content>
    </Dialog>
  );
};

export default InviteFriendsModal;
