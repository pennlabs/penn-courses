import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import RangeSlider from "react-range-slider-input";
import CustomDropdown from "./CustomDropdown";
import { SliderContainer } from "./SliderSelect";
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
  const digits = e.target.value.replace(/\D/g, "").slice(0, 4);

  const hourLength = digits.length === 4 ? 2 : 1;
  const input =
    digits.length > hourLength
      ? digits.slice(0, hourLength) + ":" + digits.slice(hourLength)
      : digits;

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

  const [draft, setDraft] = useState(time);

  const updateTime = next => {
    timeRef.current = next;
    setTime(next);
    setDraft(next);
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
    formatMinutesForDisplay(draft.start).time
  );
  const [endText, setEndText] = useState(
    formatMinutesForDisplay(draft.end).time
  );

  useEffect(() => {
    setStartText(formatMinutesForDisplay(draft.start).time);
  }, [draft.start]);

  useEffect(() => {
    setEndText(formatMinutesForDisplay(draft.end).time);
  }, [draft.end]);

  const startAMPM = formatMinutesForDisplay(draft.start).ampm;
  const endAMPM = formatMinutesForDisplay(draft.end).ampm;

  const isRangeError = !isValidRange(draft.start, draft.end);
  const isStartError = !isValid12HourTime(startText) || isRangeError;
  const isEndError = !isValid12HourTime(endText) || isRangeError;

  const applyDraft = next => {
    if (isValidRange(next.start, next.end)) {
      updateTime(next);
      commitTime(next);
    } else {
      setDraft(next);
    }
  };

  // Searching on every step would fire a request per 5 minutes dragged, so drags only
  // commit when released. Keyboard changes have no drag and commit right away.
  const onSliderInput = ([sliderStart, sliderEnd]) => {
    if (sliderEnd - sliderStart < SLIDER_STEP) {
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
                  if (isValid12HourTime(fixedValue)) {
                    setStartText(fixedValue);
                    applyDraft({
                      start: ampmTimeToMinutes(fixedValue, startAMPM),
                      end: draft.end
                    });
                  } else {
                    setStartText(formatMinutesForDisplay(draft.start).time);
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
                applyDraft({
                  start: ampmTimeToMinutes(
                    formatMinutesForDisplay(draft.start).time,
                    option
                  ),
                  end: draft.end
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
                  if (isValid12HourTime(fixedValue)) {
                    setEndText(fixedValue);
                    applyDraft({
                      start: draft.start,
                      end: ampmTimeToMinutes(fixedValue, endAMPM)
                    });
                  } else {
                    setEndText(formatMinutesForDisplay(draft.end).time);
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
                applyDraft({
                  start: draft.start,
                  end: ampmTimeToMinutes(
                    formatMinutesForDisplay(draft.end).time,
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
