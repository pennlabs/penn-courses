import React, { useContext, useEffect, useRef, useState } from "react";
import styled from "@emotion/styled";
import { NotificationsContext } from "@/components/Toast/Notifications";

const Wrapper = styled.div`
  position: relative;
  flex-shrink: 0;
`;

const BellButton = styled.button<{ $isOpen: boolean }>`
  position: relative;
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: none;
  border-radius: 50%;
  background: ${(props) =>
    props.$isOpen ? "rgba(61, 65, 119, 0.08)" : "transparent"};
  color: var(--primary-color-ultra-dark);
  font-size: 1.05rem;
  cursor: pointer;

  &:hover {
    background: rgba(61, 65, 119, 0.08);
  }
`;

const Badge = styled.span`
  position: absolute;
  top: 0.15rem;
  right: 0.1rem;
  box-sizing: border-box;
  min-width: 1rem;
  height: 1rem;
  padding: 0 0.25rem;
  border-radius: 999px;
  background: #c45c5c;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 1rem;
  text-align: center;
`;

const Panel = styled.div`
  position: absolute;
  top: calc(100% + 0.55rem);
  right: 0;
  z-index: 10050;
  display: flex;
  flex-direction: column;
  width: min(22rem, calc(100vw - 1.5rem));
  max-height: min(22rem, 60vh);
  overflow: hidden;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 28px rgba(61, 65, 119, 0.18),
    0 0 0 1px rgba(61, 65, 119, 0.08);
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 0.9rem;
  border-bottom: 1px solid #ececf3;
  color: var(--primary-color-ultra-dark);
  font-size: 0.95rem;
`;

const ClearButton = styled.button`
  padding: 0.2rem 0.35rem;
  border: none;
  border-radius: 4px;
  background: none;
  color: var(--primary-color-xxx-dark);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;

  &:hover {
    background: var(--primary-color-light);
  }
`;

const Empty = styled.div`
  padding: 1.5rem 1rem;
  color: #9a9a9a;
  font-size: 0.9rem;
  text-align: center;
`;

const List = styled.ul`
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
`;

const Item = styled.li<{ $unread: boolean }>`
  padding: 0.75rem 0.9rem;
  border-bottom: 1px solid #f2f2f6;
  background: ${(props) =>
    props.$unread ? "var(--primary-color-light)" : "transparent"};

  &:last-child {
    border-bottom: none;
  }

  time {
    font-size: 0.75rem;
    color: #9a9a9a;
  }
`;

const Message = styled.p<{ $error: boolean }>`
  margin: 0 0 0.3rem;
  font-size: 0.88rem;
  line-height: 1.35;
  color: ${(props) => (props.$error ? "var(--error-color)" : "#3a3a3a")};
`;

const timeAgo = (createdAt: number, now: number) => {
  const minutes = Math.floor((now - createdAt) / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  return new Date(createdAt).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
};

const NotificationBell = () => {
  const { notifications, markAllRead, clear } = useContext(
    NotificationsContext
  );
  const [open, setOpen] = useState(false);
  // What was unread when it was seen, so it stays highlighted while the panel is open.
  const [newIds, setNewIds] = useState<Set<number>>(new Set());
  const wrapperRef = useRef<HTMLDivElement>(null);
  const unread = notifications.filter((notification) => !notification.read)
    .length;

  useEffect(() => {
    if (!open) return undefined;
    const close = (e: MouseEvent) => {
      if (!wrapperRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  useEffect(() => {
    if (!open || !unread) return;
    const fresh = notifications.filter((n) => !n.read).map((n) => n.id);
    setNewIds((ids) => new Set([...ids, ...fresh]));
    markAllRead();
  }, [open, unread, notifications, markAllRead]);

  const now = Date.now();
  return (
    <Wrapper ref={wrapperRef}>
      <BellButton
        type="button"
        $isOpen={open}
        aria-label={
          unread ? `Notifications, ${unread} unread` : "Notifications"
        }
        aria-expanded={open}
        onClick={() => {
          if (!open) setNewIds(new Set());
          setOpen(!open);
        }}
      >
        <i className="fas fa-bell" aria-hidden />
        {unread > 0 && <Badge>{unread > 9 ? "9+" : unread}</Badge>}
      </BellButton>
      {open && (
        <Panel role="dialog" aria-label="Notifications">
          <Header>
            <strong>Notifications</strong>
            {notifications.length > 0 && (
              <ClearButton type="button" onClick={clear}>
                Clear all
              </ClearButton>
            )}
          </Header>
          {notifications.length === 0 ? (
            <Empty>No notifications yet.</Empty>
          ) : (
            <List>
              {notifications.map((notification) => (
                <Item
                  key={notification.id}
                  $unread={newIds.has(notification.id)}
                >
                  <Message $error={notification.error}>
                    {notification.message}
                  </Message>
                  <time
                    dateTime={new Date(notification.createdAt).toISOString()}
                  >
                    {timeAgo(notification.createdAt, now)}
                  </time>
                </Item>
              ))}
            </List>
          )}
        </Panel>
      )}
    </Wrapper>
  );
};

export default NotificationBell;
