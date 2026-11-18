import React, { PropsWithChildren, useEffect, useRef } from "react";
import styled from "@emotion/styled";
import { keyframes } from "@emotion/react";

const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const rise = keyframes`
  from { opacity: 0; transform: translateY(12px) scale(0.97); }
  to { opacity: 1; transform: none; }
`;

const Backdrop = styled.div`
  position: fixed;
  inset: 0;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(61, 65, 119, 0.35);
  backdrop-filter: blur(2px);
  animation: ${fadeIn} 160ms ease-out;
`;

const Card = styled.div<{ $width: string }>`
  position: relative;
  width: 100%;
  max-width: ${(props) => props.$width};
  max-height: calc(100dvh - 32px);
  overflow-y: auto;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 20px 50px rgba(61, 65, 119, 0.25);
  animation: ${rise} 240ms cubic-bezier(0.2, 0.9, 0.3, 1.2);

  &:focus {
    outline: none;
  }

  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const CloseButton = styled.button`
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  z-index: 1;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--primary-color-ultra-dark);
  cursor: pointer;

  &:hover {
    background: var(--primary-color-light);
  }
`;

export const DialogContent = styled.div`
  padding: 2rem 1.5rem 1.5rem;
  text-align: center;
`;

export const DialogTitle = styled.h2`
  margin: 0 0 0.35rem;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--primary-color-ultra-dark);
`;

export const DialogSubtitle = styled.p`
  margin: 0 auto 1.25rem;
  max-width: 19rem;
  font-size: 0.9rem;
  line-height: 1.45;
  color: var(--text-color);
`;

export const DialogButtons = styled.div`
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
`;

export const DialogButton = styled.button<{
  $quiet?: boolean;
  $danger?: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  height: 2.5rem;
  padding: 0 1.3rem;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  color: ${(props) =>
    props.$quiet ? "var(--primary-color-xxx-dark)" : "#fff"};
  background: ${(props) =>
    props.$quiet
      ? "transparent"
      : props.$danger
      ? "var(--error-color)"
      : "var(--primary-color-xxx-dark)"};
  transition: background 150ms ease, filter 150ms ease, transform 100ms ease;

  &:hover:not(:disabled) {
    background: ${(props) =>
      props.$quiet
        ? "var(--primary-color-light)"
        : props.$danger
        ? "var(--error-color)"
        : "var(--primary-color-ultra-dark)"};
    filter: ${(props) => (props.$danger ? "brightness(0.92)" : "none")};
  }
  &:active:not(:disabled) {
    transform: scale(0.97);
  }
  &:disabled {
    opacity: 0.5;
    cursor: default;
  }
`;

export const DialogInput = styled.input`
  width: 100%;
  height: 2.6rem;
  padding: 0 1rem;
  border-radius: 999px;
  border: 2px solid transparent;
  outline: none;
  background: var(--background-grey);
  font: inherit;
  font-size: 0.95rem;
  color: var(--primary-color-ultra-dark);
  transition: border-color 150ms ease, background 150ms ease;

  &:focus {
    background: #fff;
    border-color: var(--primary-color-dark);
  }
  &::placeholder {
    color: var(--primary-color-extra-dark);
  }
`;

interface DialogProps {
  close: () => void;
  label: string;
  width?: string;
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * A centered card over a blurred page, closed by its ✕, Escape, or a click outside it. Focus
 * moves into it, Tab stays within it, and closing returns focus to where it was.
 */
const Dialog = ({
  close,
  label,
  width = "25rem",
  children,
}: PropsWithChildren<DialogProps>) => {
  const card = useRef<HTMLDivElement>(null);
  // Read on the first render, before anything inside autofocuses.
  const returnTo = useRef(
    typeof document === "undefined"
      ? null
      : (document.activeElement as HTMLElement | null)
  );

  useEffect(() => {
    if (card.current && !card.current.contains(document.activeElement))
      card.current.focus();
    const opener = returnTo.current;
    return () => {
      if (opener?.isConnected) opener.focus();
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key !== "Tab" || !card.current) return;
      const focusable = [
        ...card.current.querySelectorAll<HTMLElement>(FOCUSABLE),
      ];
      if (!focusable.length) {
        e.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const inside = card.current.contains(document.activeElement);
      if (e.shiftKey && (document.activeElement === first || !inside)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (document.activeElement === last || !inside)) {
        e.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [close]);

  return (
    <Backdrop
      // Pressing on the backdrop itself, so a text selection dragged out of the card doesn't close it.
      onMouseDown={(e) => e.target === e.currentTarget && close()}
    >
      <Card
        ref={card}
        role="dialog"
        aria-modal="true"
        aria-label={label}
        tabIndex={-1}
        $width={width}
      >
        <CloseButton type="button" aria-label="Close" onClick={close}>
          <i className="fas fa-times" aria-hidden />
        </CloseButton>
        {children}
      </Card>
    </Backdrop>
  );
};

export default Dialog;
