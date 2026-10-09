import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import RangeSlider from "react-range-slider-input";
import CustomDropdown from "./CustomDropdown";
import { RangeMarkers, SliderContainer } from "./SliderSelect";
import { DEFAULT_FILTERS, normalizeTimeString } from "../utils/filters";

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

const SLIDER_STEP = 5;
const SLIDER_MAX = 1440;
const LAST_MINUTE = 1439;

const toSliderMinutes = m => (m === LAST_MINUTE ? SLIDER_MAX : m);
const fromSliderMinutes = m => Math.min(m, LAST_MINUTE);

// Start must come before end, at least one slider step apart
const isValidRange = (start, end) =>
  toSliderMinutes(end) - toSliderMinutes(start) >= SLIDER_STEP;

const stringToMinutes = timeString => {
  const safe = normalizeTimeString(timeString) || DEFAULT_FILTERS.time;
  const [start, end] = safe.split("-");
  const [startHours, startMinutes] = start.split(".").map(Number);
  const [endHours, endMinutes] = end.split(".").map(Number);
  return {
    start: startHours * 60 + startMinutes,
    end: endHours * 60 + endMinutes
  };
};

const formatMinutes = m =>
  `${Math.floor(m / 60)}.${String(m % 60).padStart(2, "0")}`;

const formatMinutesForDisplay = m => {
  const hours = Math.floor(m / 60);
  const minutes = m % 60;
  const ampm = hours >= 12 ? "PM" : "AM";
  const displayHours = hours > 12 ? hours - 12 : hours;
  return {
    time: `${displayHours === 0 ? 12 : displayHours}:${String(minutes).padStart(
      2,
      "0"
    )}`,
    ampm: ampm
  };
};

const ampmTimeToMinutes = (value, ampm) => {
  const hours = Number(value.split(":")[0]);
  const minutes = Number(value.split(":")[1] || "00");
  const correctedHours =
    ampm === "PM" && hours !== 12
      ? hours + 12
      : ampm === "AM" && hours === 12
      ? 0
      : hours;
  return correctedHours * 60 + minutes;
};

const handleTimeInputChange = (e, setTextState) => {
  let input = e.target.value;

  input = input.replace(/[^\d:]/g, "");

  const parts = input.split(":");
  if (parts.length > 2) {
    input = parts[0] + ":" + parts[1];
  }

  if (parts[0].length > 2) {
    const firstHalf = parts[0].slice(0, 2);
    const secondHalf = parts[0].slice(2);
    input =
      firstHalf +
      (secondHalf ? ":" + secondHalf : "") +
      (parts[1] ? ":" + parts[1] : "");
  }
  if (parts.length > 1 && parts[1].length > 2) {
    input = parts[0] + ":" + parts[1].slice(0, 2);
  }

  setTextState(input);
};

const fixTimeInputOnBlur = input => {
  let [hours, minutes] = input.split(":");
  minutes = minutes ? minutes.padStart(2, "0") : "00";
  return `${hours}:${minutes}`;
};

const isValid12HourTime = timeString => {
  // If it's empty, we won't yell at them just yet
  if (!timeString) return true;

  const parts = timeString.split(":");
  const hours = parseInt(parts[0], 10);
  const minutes = parts.length > 1 ? parseInt(parts[1], 10) : 0;

  // Check if hours > 12 or minutes > 59
  if (hours > 12) return false;
  if (parts.length > 1 && minutes > 59) return false;

  return true;
};

const TimeSelect = ({ timeString, setTimeString }) => {
  const [time, setTime] = useState(() => stringToMinutes(timeString));

  // Refs so the slider's drag callbacks always see the latest values
  const timeRef = useRef(time);
  const timeStringRef = useRef(timeString);
  const isDragging = useRef(false);
  useEffect(() => {
    timeStringRef.current = timeString;
  }, [timeString]);

  const updateTime = next => {
    timeRef.current = next;
    setTime(next);
  };

  const commitTime = next => {
    const newTime = `${formatMinutes(next.start)}-${formatMinutes(next.end)}`;
    if (newTime !== timeStringRef.current) {
      setTimeString(newTime);
    }
  };

  useEffect(() => {
    const next = stringToMinutes(timeString);
    const current = timeRef.current;
    if (next.start !== current.start || next.end !== current.end) {
      updateTime(next);
    }
  }, [timeString]);

  const [startText, setStartText] = useState(
    formatMinutesForDisplay(time.start).time
  );
  const [endText, setEndText] = useState(
    formatMinutesForDisplay(time.end).time
  );

  useEffect(() => {
    setStartText(formatMinutesForDisplay(time.start).time);
  }, [time.start]);

  useEffect(() => {
    setEndText(formatMinutesForDisplay(time.end).time);
  }, [time.end]);

  const startAMPM = formatMinutesForDisplay(time.start).ampm;
  const endAMPM = formatMinutesForDisplay(time.end).ampm;

  const isStartError = !isValid12HourTime(startText);
  const isEndError = !isValid12HourTime(endText);

  // Applies a typed or AM/PM change, returning whether it was a valid range
  const applyTime = next => {
    if (!isValidRange(next.start, next.end)) return false;
    updateTime(next);
    commitTime(next);
    return true;
  };

  // Searching on every step would fire a request per 5 minutes dragged, so drags only
  // commit when released. Keyboard changes have no drag and commit right away.
  const onSliderInput = ([sliderStart, sliderEnd]) => {
    if (sliderEnd - sliderStart < SLIDER_STEP) {
      // Re-render with a fresh object so the slider snaps back to the last valid range
      updateTime({ ...timeRef.current });
      return;
    }
    const next = {
      start: fromSliderMinutes(sliderStart),
      end: fromSliderMinutes(sliderEnd)
    };
    updateTime(next);
    if (!isDragging.current) commitTime(next);
  };

  const onDragStart = () => {
    isDragging.current = true;
  };

  const onDragEnd = () => {
    isDragging.current = false;
    commitTime(timeRef.current);
  };

  return (
    <>
    <Container>
      <TimeInputContainer>
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center"
            }}
          >
            <span style={{ fontSize: "12px" }}>Start</span>
            <form
              onSubmit={e => {
                e.preventDefault();
                const fixedValue = fixTimeInputOnBlur(startText);
                setStartText(fixedValue);
                if (
                  !isValid12HourTime(fixedValue) ||
                  !applyTime({
                    start: ampmTimeToMinutes(fixedValue, startAMPM),
                    end: time.end
                  })
                ) {
                  setStartText(formatMinutesForDisplay(time.start).time);
                }
                e.target.querySelector("input").blur();
              }}
            >
              <TimeInput
                type="text"
                value={startText}
                $isError={isStartError}
                onChange={e => {
                  handleTimeInputChange(e, setStartText);
                }}
                onBlur={e => {
                  e.target.form.requestSubmit();
                }}
              />
            </form>
          </div>
          <CustomDropdown
            style={{ width: "60px", marginTop: "18px" }}
            options={["AM", "PM"]}
            value={startAMPM}
            onChange={option => {
              applyTime({
                start: ampmTimeToMinutes(
                  formatMinutesForDisplay(time.start).time,
                  option
                ),
                end: time.end
              });
            }}
          />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center"
            }}
          >
            <span style={{ fontSize: "12px" }}>End</span>
            <form
              onSubmit={e => {
                e.preventDefault();
                const fixedValue = fixTimeInputOnBlur(endText);
                setEndText(fixedValue);
                if (
                  !isValid12HourTime(fixedValue) ||
                  !applyTime({
                    start: time.start,
                    end: ampmTimeToMinutes(fixedValue, endAMPM)
                  })
                ) {
                  setEndText(formatMinutesForDisplay(time.end).time);
                }
                e.target.querySelector("input").blur();
              }}
            >
              <TimeInput
                type="text"
                value={endText}
                $isError={isEndError}
                onChange={e => {
                  handleTimeInputChange(e, setEndText);
                }}
                onBlur={e => {
                  e.target.form.requestSubmit();
                }}
              />
            </form>
          </div>
          <CustomDropdown
            style={{ width: "60px", marginTop: "18px" }}
            options={["AM", "PM"]}
            value={endAMPM}
            onChange={option => {
              applyTime({
                start: time.start,
                end: ampmTimeToMinutes(
                  formatMinutesForDisplay(time.end).time,
                  option
                )
              });
            }}
          />
        </div>
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
            value={[toSliderMinutes(time.start), toSliderMinutes(time.end)]}
            onInput={onSliderInput}
            onThumbDragStart={onDragStart}
            onThumbDragEnd={onDragEnd}
            onRangeDragStart={onDragStart}
            onRangeDragEnd={onDragEnd}
            ariaLabel={["Start time", "End time"]}
          />
        </SliderContainer>
        <RangeMarkers>
          <div>12 AM</div>
          <div>12 PM</div>
          <div>11:59 PM</div>
        </RangeMarkers>
      </div>
      </>
  );
};

export default TimeSelect;
