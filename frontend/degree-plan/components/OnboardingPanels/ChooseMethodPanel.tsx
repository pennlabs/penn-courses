import { keyframes } from "@emotion/react";
import styled from "@emotion/styled";
import { ArrowLeftIcon, ArrowRightIcon } from "@radix-ui/react-icons";
import { color } from "./onboardingStyles";
import {
  CenteredFlexContainer,
  ChooseContainer,
  ExitButton,
  WelcomeTitle,
} from "./SharedComponents";

const jackhammer = keyframes`
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(-1px, 1px); }
  50% { transform: translate(1px, -1px); }
  75% { transform: translate(-1px, -1px); }
`;

const bob = keyframes`
  0%, 100% { transform: rotate(0deg) translateY(0); }
  50% { transform: rotate(-3deg) translateY(2px); }
`;

const Subtitle = styled.p`
  margin: -28px 0 0;
  color: ${color.muted};
  font-size: 1.05rem;
  text-align: center;

  @media (max-width: 767px) {
    margin-top: -12px;
  }
`;

const Options = styled.div`
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 20px;
  width: min(900px, 100%);
  padding: 0 24px 40px;
  box-sizing: border-box;

  @media (max-width: 767px) {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 0;
  }
`;

const Or = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary-color-light);
  color: var(--primary-color-xxx-dark);
  font-size: 0.85rem;
  font-weight: 700;
  justify-self: center;

  @media (max-width: 767px) {
    width: 36px;
    height: 36px;
  }
`;

// Both poses are stacked in the same spot, so swapping them never shifts the layout and the
// second one is already loaded when the card is hovered.
const Pose = styled.img`
  grid-area: 1 / 1;
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: opacity 0.15s ease;
`;

const Art = styled.div`
  position: relative;
  display: grid;
  width: min(230px, 100%);
  aspect-ratio: 254 / 194;

  .pose-active {
    opacity: 0;
  }

  @media (max-width: 767px) {
    width: 150px;
  }
`;

const Shadow = styled.span`
  position: absolute;
  left: 12%;
  right: 12%;
  bottom: -6px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary-color-dark);
  opacity: 0.6;
  z-index: -1;
  transition: transform 0.2s ease;
`;

const OptionTitle = styled.span`
  margin-top: 8px;
  font-size: 1.25rem;
  font-weight: 700;
  color: ${color.heading};
`;

const OptionText = styled.span`
  max-width: 290px;
  color: ${color.muted};
  font-size: 0.9rem;
  line-height: 1.45;
`;

const Go = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  padding: 6px 14px;
  border-radius: 999px;
  background: #ffffff;
  color: var(--primary-color-xxx-dark);
  font-size: 0.9rem;
  font-weight: 700;
  transition: gap 0.15s ease, background-color 0.15s ease, color 0.15s ease;
`;

const Option = styled.button<{ $wiggle: typeof jackhammer }>`
  isolation: isolate;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  height: 100%;
  padding: 28px 24px 24px;
  border: 2px solid var(--primary-color);
  border-radius: 24px;
  background: var(--primary-color-extra-light);
  font: inherit;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease,
    background-color 0.2s ease;

  &:hover,
  &:focus-visible {
    border-color: var(--primary-color-xx-dark);
    background: var(--primary-color-light);
    box-shadow: 0 10px 24px rgba(61, 65, 119, 0.12);
    transform: translateY(-4px) rotate(-0.5deg);
  }

  &:focus-visible {
    outline: none;
  }

  &:hover .pose-rest,
  &:focus-visible .pose-rest,
  &:active .pose-rest {
    opacity: 0;
  }

  &:hover .pose-active,
  &:focus-visible .pose-active,
  &:active .pose-active {
    opacity: 1;
    animation: ${({ $wiggle }) => $wiggle} 0.5s ease-in-out infinite;
  }

  &:hover .shadow,
  &:focus-visible .shadow {
    transform: scaleX(1.08);
  }

  &:hover .go,
  &:focus-visible .go {
    gap: 10px;
    background: var(--primary-color-xxx-dark);
    color: #ffffff;
  }

  @media (prefers-reduced-motion: reduce) {
    transition: none;
    &:hover,
    &:focus-visible {
      transform: none;
    }
    .pose-rest,
    .pose-active,
    .shadow,
    .go {
      transition: none;
      animation: none !important;
    }
  }

  @media (max-width: 767px) {
    padding: 20px 16px;
  }
`;

type OptionCardProps = {
  wiggle: typeof jackhammer;
  rest: string;
  active: string;
  title: string;
  go: string;
  onClick: () => void;
  children: React.ReactNode;
};

const OptionCard = ({
  wiggle,
  rest,
  active,
  title,
  go,
  onClick,
  children,
}: OptionCardProps) => (
  <Option type="button" onClick={onClick} $wiggle={wiggle}>
    <Art>
      <Shadow className="shadow" />
      <Pose className="pose-rest" src={rest} alt="" />
      <Pose className="pose-active" src={active} alt="" />
    </Art>
    <OptionTitle>{title}</OptionTitle>
    <OptionText>{children}</OptionText>
    <Go className="go">
      {go}
      <ArrowRightIcon />
    </Go>
  </Option>
);

type ChooseMethodPanelProps = {
  onTranscript: () => void;
  onManual: () => void;
  canExit?: boolean;
  onExit?: () => void;
};

export default function ChooseMethodPanel({
  onTranscript,
  onManual,
  canExit = false,
  onExit,
}: ChooseMethodPanelProps) {
  return (
    <CenteredFlexContainer>
      <ChooseContainer $maxWidth="90%" $minWidth="90%">
        {canExit && onExit && (
          <ExitButton type="button" onClick={onExit}>
            <ArrowLeftIcon width={16} height={16} />
            Back
          </ExitButton>
        )}
        <WelcomeTitle>Welcome to Penn Degree Plan!</WelcomeTitle>
        <Subtitle>How would you like to add your courses?</Subtitle>
        <Options>
          <OptionCard
            wiggle={jackhammer}
            rest="/porcupine-jackhammer-ready.svg"
            active="/porcupine-jackhammer-drilling.svg"
            title="Upload your transcript"
            go="Choose a PDF"
            onClick={onTranscript}
          >
            We&apos;ll pull your courses, programs and years from your
            unofficial transcript. It&apos;s read on your computer and never
            uploaded.
          </OptionCard>
          <Or>or</Or>
          <OptionCard
            wiggle={bob}
            rest="/porcupine-archaeologist-ready.svg"
            active="/porcupine-archaeologist-digging.svg"
            title="Add courses yourself"
            go="Start from scratch"
            onClick={onManual}
          >
            Pick your school, programs and years, then add the courses
            you&apos;ve taken and plan to take.
          </OptionCard>
        </Options>
      </ChooseContainer>
    </CenteredFlexContainer>
  );
}
