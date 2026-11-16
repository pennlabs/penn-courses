import React, { useEffect, useState } from "react";
import styled from "@emotion/styled";
import { keyframes } from "@emotion/react";

const appear = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const Container = styled.div`
  flex: 1;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  /* Quick loads finish before it shows, so it doesn't flash. */
  animation: ${appear} 0.2s ease 0.15s both;
`;

const Porcupine = styled.img`
  width: 16rem;
  max-width: 80%;
`;

const Message = styled.div`
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #8a8a8a;
  animation: ${appear} 0.3s ease;
`;

const PorcupineLoader = ({ src, messages }: { src: string; messages: string[] }) => {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (messages.length < 2) return;
    const timer = setInterval(() => setIndex((i) => (i + 1) % messages.length), 1800);
    return () => clearInterval(timer);
  }, [messages.length]);

  return (
    <Container role="status">
      <Porcupine src={src} alt="" />
      <Message key={index}>{messages[index % messages.length]}</Message>
    </Container>
  );
};

export default PorcupineLoader;
