import { keyframes } from "@emotion/react";
import styled from "@emotion/styled";
import { IconProps, toast } from "react-toastify";

const GROUP_WINDOW_MS = 200;
const MAX_LINES = 4;

const Headline = styled.div`
  font-weight: 600;
`;

const Lines = styled.ul`
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
  color: var(--primary-color-xxx-dark);
  font-size: 0.8rem;
  line-height: 1.4;
`;

const pop = keyframes`
  0% { transform: scale(0.6); }
  60% { transform: scale(1.12); }
  100% { transform: scale(1); }
`;

const Mark = styled.span<{ $error: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: ${({ $error }) =>
    $error ? "#fbe9e8" : "var(--primary-color-light)"};
  color: ${({ $error }) =>
    $error ? "var(--error-color)" : "var(--primary-color-xxx-dark)"};
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  animation: ${pop} 0.35s ease-out;
`;

export const ToastIcon = ({ type }: IconProps) => {
  const error = type === "error";
  return <Mark $error={error}>{error ? "!" : "\u2713"}</Mark>;
};

const ToastBody = ({ messages }: { messages: string[] }) => {
  const [first, ...rest] = messages;
  const shown = rest.slice(0, MAX_LINES);
  const hidden = rest.length - shown.length;
  return (
    <>
      <Headline>{first}</Headline>
      {shown.length > 0 && (
        <Lines>
          {shown.map((message) => (
            <li key={message}>{message}</li>
          ))}
          {hidden > 0 && <li>and {hidden} more</li>}
        </Lines>
      )}
    </>
  );
};

const pending = { success: [] as string[], error: [] as string[] };
let timer: ReturnType<typeof setTimeout> | null = null;

const flush = () => {
  timer = null;
  (["error", "success"] as const).forEach((kind) => {
    const messages = pending[kind];
    pending[kind] = [];
    if (!messages.length) return;
    const body = <ToastBody messages={messages} />;
    if (kind === "error") toast.error(body);
    else toast.success(body);
  });
};

export const queueToast = (text: string, error: boolean) => {
  const list = pending[error ? "error" : "success"];
  if (!list.includes(text)) list.push(text);
  if (!timer) timer = setTimeout(flush, GROUP_WINDOW_MS);
};
