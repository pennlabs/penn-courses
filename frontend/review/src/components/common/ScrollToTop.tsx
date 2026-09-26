import React, { useCallback, useEffect, useRef, useState } from "react";
import styled from "styled-components";
import { FaArrowUp } from "react-icons/fa";
import { maxWidth } from "../../styles/media";
import { unstyledButton } from "../../styles/mixins";

interface ScrollToTopProps {
  // How far a scroll container has to travel before the button appears.
  threshold?: number;
  className?: string;
}

const Button = styled.button<{ $visible: boolean }>`
  ${unstyledButton}

  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 14px;
  border: 1px solid ${({ theme }) => theme.color.border.default};
  border-radius: ${({ theme }) => theme.radius.pill};
  background: ${({ theme }) => theme.color.surface.page};
  color: ${({ theme }) => theme.color.text.secondary};
  font-size: ${({ theme }) => theme.font.size.md};
  box-shadow: ${({ theme }) => theme.shadow.card};

  // visibility is transitioned so the button stays rendered until the fade-out ends
  transition: opacity ${({ theme }) => theme.motion.duration.md}
      ${({ theme }) => theme.motion.ease.standard},
    transform ${({ theme }) => theme.motion.duration.md}
      ${({ theme }) => theme.motion.ease.emphasized},
    background-color ${({ theme }) => theme.motion.duration.fast}
      ${({ theme }) => theme.motion.ease.standard},
    visibility ${({ theme }) => theme.motion.duration.md};

  opacity: ${({ $visible }) => ($visible ? 1 : 0)};
  transform: translateY(${({ $visible }) => ($visible ? "0" : "8px")});
  pointer-events: ${({ $visible }) => ($visible ? "auto" : "none")};
  visibility: ${({ $visible }) => ($visible ? "visible" : "hidden")};

  &:hover {
    background: ${({ theme }) => theme.color.surface.subtle};
    color: ${({ theme }) => theme.color.text.primary};
  }

  /* A circular floating button once there is no room for the label. */
  ${maxWidth("lg")} {
    width: 46px;
    height: 46px;
    padding: 0;
    border-radius: ${({ theme }) => theme.radius.circle};
  }
`;

const Label = styled.span`
  ${maxWidth("lg")} {
    display: none;
  }
`;

/*
  Scroll events don't bubble, so we listen in the capture phase to pick up every
  scroll container on the page (the results table's own scroll area on desktop,
  the stacked page column on mobile, and the window itself) without having to
  thread refs through the components that own them.
*/
const ScrollToTop = ({ threshold = 240, className }: ScrollToTopProps) => {
  const [visible, setVisible] = useState(false);
  const scrollersRef = useRef<Set<Element>>(new Set());

  useEffect(() => {
    const scrollers = scrollersRef.current;

    const handleScroll = (event: Event) => {
      const { target } = event;
      if (target instanceof Element) scrollers.add(target);

      // The results panel is remounted whenever the filters change, so forget
      // containers that are no longer in the document.
      scrollers.forEach((el) => {
        if (!el.isConnected) scrollers.delete(el);
      });

      setVisible(
        window.scrollY > threshold ||
          Array.from(scrollers).some((el) => el.scrollTop > threshold)
      );
    };

    document.addEventListener("scroll", handleScroll, true);
    return () => document.removeEventListener("scroll", handleScroll, true);
  }, [threshold]);

  const handleClick = useCallback(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    scrollersRef.current.forEach((el) => {
      if (el.isConnected) el.scrollTo({ top: 0, behavior: "smooth" });
    });
  }, []);

  return (
    <Button
      type="button"
      className={className}
      $visible={visible}
      onClick={handleClick}
      tabIndex={visible ? 0 : -1}
      aria-hidden={!visible}
      aria-label="Scroll back to top"
    >
      <FaArrowUp size={14} />
      <Label>Back to top</Label>
    </Button>
  );
};

export default ScrollToTop;
