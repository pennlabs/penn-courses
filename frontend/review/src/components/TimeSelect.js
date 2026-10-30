import React, { useState } from "react";
import styled from "styled-components";
import RangeSlider from "react-range-slider-input";
import CustomDropdown from "./CustomDropdown";
import { SliderContainer } from "./SliderSelect";
import { DEFAULT_FILTERS, normalizeTimeString } from "../utils/filters";
import { useSliderCommit } from "../utils/hooks";

const Container = styled.div`
  display: flex;
  padding: 12px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  align-self: stretch;
`;

const TimeInputContainer = styled.div`
  display: flex;
  align-self: center;
  justify-content: space-between;
  width: 100%;
  max-width: 300px;
`;

const TimeInput = styled.input`
  all: unset;
  text-align: center;
  font-size: 14px;
  font-family: ${({ theme }) => theme.font.family.sans};
  padding: 2px;
  border: 2px solid
    ${props =>
      props.$isError
        ? "var(--pcr-color-feedback-error-fg)"
        : "var(--pcr-color-border-input)"};
  border-radius: 8px;
  background-color: ${props =>
    props.$isError ? "var(--pcr-color-feedback-error-bg)" : "transparent"};
  width: 50px;

  &:focus {
    border: 2px solid
      ${props =>
        props.$isError
          ? "var(--pcr-color-feedback-error-fg)"
          : "var(--pcr-color-border-focus)"};
    background-color: ${props =>
      props.$isError ? "var(--pcr-color-feedback-error-bg)" : "transparent"};
  }
`;

const ExtendedRangeMarkers = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  align-self: stretch;
  font-size: 12px;
  font-family: ${({ theme }) => theme.font.family.sans};
  font-weight: ${({ theme }) => theme.font.weight.bold};
  margin: 15px 3% 0 3%;
`;

const SLIDER_STEP = 5;
const SLIDER_MAX = 1440;
const LAST_MINUTE = 1439;

const toSlider = m => (m === LAST_MINUTE ? SLIDER_MAX : m);
const fromSlider = m => Math.min(m, LAST_MINUTE);

const isValidRange = ({ start, end }) =>
  toSlider(end) - toSlider(start) >= SLIDER_STEP;

// "9.30-17.00" <-> { start: 570, end: 1020 }, in minutes since midnight
const parseTimeString = timeString => {
  const [start, end] = (normalizeTimeString(timeString) || DEFAULT_FILTERS.time)
    .split("-")
    .map(t => {
      const [hours, minutes] = t.split(".").map(Number);
      return hours * 60 + minutes;
    });
  return { start, end };
};

const formatTimeString = ({ start, end }) =>
  [start, end]
    .map(m => `${Math.floor(m / 60)}.${String(m % 60).padStart(2, "0")}`)
    .join("-");

const to12h = m => {
  const hours = Math.floor(m / 60);
  return {
    time: `${hours % 12 || 12}:${String(m % 60).padStart(2, "0")}`,
    ampm: hours < 12 ? "AM" : "PM"
  };
};

const from12h = (time, ampm) => {
  const [hours, minutes] = time.split(":").map(Number);
  return ((hours % 12) + (ampm === "PM" ? 12 : 0)) * 60 + minutes;
};

// Accepts "9", "9:3" or "9:30" while typing; a missing minute counts as :00
const isValid12h = text => {
  const [hours, minutes = "0"] = text.split(":");
  return hours >= 1 && hours <= 12 && minutes <= 59;
};

// Digits only, with the colon placed for the user: "930" -> "9:30", "1130" -> "11:30"
const formatTyping = value => {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  const hourLength = digits.length === 4 ? 2 : 1;
  return digits.length > hourLength
    ? `${digits.slice(0, hourLength)}:${digits.slice(hourLength)}`
    : digits;
};

const TimeField = ({ label, minutes, isRangeError, onChange }) => {
  const [text, setText] = useState(null);
  const { time, ampm } = to12h(minutes);

  const apply = () => {
    if (text && isValid12h(text)) {
      const [hours, mins = "00"] = text.split(":");
      onChange(from12h(`${hours}:${mins.padStart(2, "0")}`, ampm));
    }
    setText(null);
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center"
        }}
      >
        <span style={{ fontSize: "12px" }}>{label}</span>
        <TimeInput
          type="text"
          aria-label={`${label} time`}
          value={text ?? time}
          $isError={isRangeError || (!!text && !isValid12h(text))}
          onChange={e => setText(formatTyping(e.target.value))}
          onBlur={apply}
          onKeyDown={e => e.key === "Enter" && e.target.blur()}
        />
      </div>
      <CustomDropdown
        style={{ width: "60px", marginTop: "18px" }}
        options={["AM", "PM"]}
        value={ampm}
        onChange={option => onChange(from12h(time, option))}
      />
    </div>
  );
};

const TimeSelect = ({ timeString, setTimeString }) => {
  //Draft before syncing with filter
  const [draft, setDraft] = useState(null);
  const value =
    draft && draft.base === timeString ? draft : parseTimeString(timeString);

  const commit = next => {
    setDraft(null);
    const nextString = formatTimeString(next);
    if (nextString !== timeString) setTimeString(nextString);
  };

  const change = next => {
    if (isValidRange(next)) commit(next);
    else setDraft({ base: timeString, ...next });
  };

  // Drags commit when released and keyboard steps are debounced, so a search doesn't
  // fire for every 5 minute step. A step queued before the value changed elsewhere is dropped.
  const { update, dragProps } = useSliderCommit(next => {
    if (next.base === timeString) commit(next);
  });

  const onSliderInput = ([start, end]) => {
    // Keep the thumbs a step apart by pushing back the one that didn't move
    if (end - start < SLIDER_STEP) {
      if (start !== toSlider(value.start)) start = end - SLIDER_STEP;
      else end = start + SLIDER_STEP;
    }
    const next = {
      base: timeString,
      start: fromSlider(start),
      end: fromSlider(end)
    };
    setDraft(next);
    update(next);
  };

  const isRangeError = !isValidRange(value);

  return (
    <>
      <Container>
        <TimeInputContainer>
          <TimeField
            label="Start"
            minutes={value.start}
            isRangeError={isRangeError}
            onChange={start => change({ start, end: value.end })}
          />
          <TimeField
            label="End"
            minutes={value.end}
            isRangeError={isRangeError}
            onChange={end => change({ start: value.start, end })}
          />
        </TimeInputContainer>
      </Container>
      <div
        style={{
          width: "100%",
          userSelect: "none",
          WebkitUserSelect: "none",
          MozUserSelect: "none",
          maxWidth: "600px"
        }}
      >
        <SliderContainer>
          <RangeSlider
            min={0}
            max={SLIDER_MAX}
            step={SLIDER_STEP}
            value={[toSlider(value.start), toSlider(value.end)]}
            onInput={onSliderInput}
            {...dragProps}
            ariaLabel={["Start time", "End time"]}
          />
        </SliderContainer>
        <ExtendedRangeMarkers>
          <div>12 AM</div>
          <div>12 PM</div>
          <div>11:59 PM</div>
        </ExtendedRangeMarkers>
      </div>
    </>
  );
};

export default TimeSelect;
