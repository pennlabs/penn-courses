import React, { useState, useEffect, useCallback, useRef, useReducer } from "react";
import styled from "styled-components";
import CustomDropdown from "./CustomDropdown";

const Container = styled.div`
    display: flex;
    padding: 12px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    align-self: stretch;
`;

const ClockFace = styled.svg`
    width: 100%;
    touch-action: none;
    cursor: ${props => props.drag ? "grabbing" : "default"};
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
    font-family: 'SFPro', sans-serif;
    padding: 2px;
    border: 2px solid ${props => props.$isError ? '#e53935' : '#aeaeb8'};
    border-radius: 8px;
    background-color: ${props => props.$isError ? '#ffebee' : 'transparent'};
    width: 50px;

    &:focus {
        border: 2px solid ${props => props.$isError ? '#e53935' : '#aeaeb8'};
        background-color: ${props => props.$isError ? '#ffebee' : 'transparent'};
    }
`;

const AMPMSelect = styled.select`
    all: unset;
    font-size: 14px;
    font-family: 'SFPro', sans-serif;
    padding: 2px;
    border-radius: 8px;
    background-color: #EFF1F5;
    width: 60px;

    &:hover {
        background-color: #E1E4E8;
    }
`;

const stringToMinutes = (timeString) => {
    const [start, end] = timeString.split('-');
    const [startHours, startMinutes] = start.split(".").map(Number);
    const [endHours, endMinutes] = end.split(".").map(Number);
    return {start: startHours * 60 + startMinutes, end: endHours * 60 + endMinutes};
}

const minutesToRadians = (minutes) => {
    return (((minutes / 1440) * 360) - 90)* (Math.PI / 180); // -90 to start at 12 o'clock (browser angles are CW, so negative)
}

const radiansToMinutes = (radians) => {
    const degrees = (radians * 180 / Math.PI + 90 + 360) % 360; // +90 to convert back, +360 to ensure positive
    let minutes = Math.round((degrees / 360) * 1440);
    minutes = Math.round(minutes / 5) * 5; // snap to nearest 5 minutes
    return minutes % 1440;
}

const formatMinutes = (m) => `${Math.floor(m / 60)}.${String(m % 60).padStart(2, "0")}`;

const formatMinutesForDisplay = (m) => {
    const hours = Math.floor(m / 60);
    const minutes = m % 60;
    const ampm = hours >= 12 ? "PM" : "AM";
    const displayHours = hours > 12 ? hours - 12 : hours;
    return {time: `${displayHours === 0 ? 12 : displayHours}:${String(minutes).padStart(2, "0")}`, ampm: ampm};
}

const ampmTimeToMinutes = (value, ampm) => {
    const hours = Number(value.split(':')[0]);
    const minutes = Number(value.split(':')[1] || '00');
    const correctedHours = (ampm === "PM" && hours !== 12) ? hours + 12 : (ampm === "AM" && hours === 12) ? 0 : hours;
    return correctedHours * 60 + minutes;
}

const handleTimeInputChange = (e, setTextState) => {
    let input = e.target.value;

    input = input.replace(/[^\d:]/g, '');

    const parts = input.split(':');
    if (parts.length > 2) {
        input = parts[0] + ':' + parts[1];
    }

    if (parts[0].length > 2) {
        const firstHalf = parts[0].slice(0, 2);
        const secondHalf = parts[0].slice(2);
        input = firstHalf + (secondHalf ? ':' + secondHalf : '') + (parts[1] ? ':' + parts[1] : '');
    }
    if (parts.length > 1 && parts[1].length > 2) {
        input = parts[0] + ':' + parts[1].slice(0, 2);
    }

    setTextState(input);
};

const fixTimeInputOnBlur = (input) => {
    let [hours, minutes] = input.split(':');
    minutes = minutes ? minutes.padStart(2, '0') : '00';
    return `${hours}:${minutes}`;
}

const isValid12HourTime = (timeString) => {
    // If it's empty, we won't yell at them just yet
    if (!timeString) return true; 

    const parts = timeString.split(':');
    const hours = parseInt(parts[0], 10);
    const minutes = parts.length > 1 ? parseInt(parts[1], 10) : 0;

    // Check if hours > 12 or minutes > 59
    if (hours > 12) return false;
    if (parts.length > 1 && minutes > 59) return false;

    return true;
};

const TimeSelect = ({ timeString, setTimeString, diameter }) => {
    const { start: initialStart, end: initialEnd } = stringToMinutes(timeString);
    const [time, dispatch] = useReducer((state, action) => {
        if (action.type === "setStart") {
            const delta = (state.end - action.minutes + 1440) % 1440;
            return delta >= 5 ? { ...state, start: action.minutes } : state;
        }
        if (action.type === "setEnd") {
            const delta = (action.minutes - state.start + 1440) % 1440;
            return delta >= 5 ? { ...state, end: action.minutes } : state;
        }
        return state;
    }, { start: initialStart, end: initialEnd });

    const timeRef = useRef(time);
    useEffect(() => { timeRef.current = time; }, [time]);

    const [drag, setDrag] = useState(null);

    const [startText, setStartText] = useState(formatMinutesForDisplay(initialStart).time);
    const [endText, setEndText] = useState(formatMinutesForDisplay(initialEnd).time);

    const clockRef = useRef(null);

    const startAMPM = formatMinutesForDisplay(time.start).ampm;
    const endAMPM = formatMinutesForDisplay(time.end).ampm;

    const viewBoxOffset = diameter/2; //extra space around the clock for ticks and labels
    const C = diameter / 2 + viewBoxOffset / 2; //center of clock in svg coordinates
    const R = diameter / 2; //safe radius for ticks and hands
    const HAND_LEN = R - 16;
    const KNOB = 8;

    const polarToCartesian = useCallback((r, a) => {
        return { x: C + r * Math.cos(a), y: C + r * Math.sin(a) };
    }, [C]);

    const arcPath = (startAngle, endAngle) => {
        let sweep = endAngle - startAngle;
        if (sweep < 0) sweep += 2 * Math.PI;
        const largeFlag = sweep > Math.PI ? 1 : 0; //if the sweep angle > 180, we need the svg to go the long way around
        const startSweepPos = polarToCartesian(R, startAngle);
        const endSweepPos = polarToCartesian(R, endAngle);
        return `M ${C} ${C} L ${startSweepPos.x} ${startSweepPos.y} A ${R} ${R} 0 ${largeFlag} 1 ${endSweepPos.x} ${endSweepPos.y} Z`;
    }

    useEffect(() => {
        setStartText(formatMinutesForDisplay(time.start).time);
    }, [time.start]);

    useEffect(() => {
        setEndText(formatMinutesForDisplay(time.end).time);
    }, [time.end]);

    useEffect(() => {
        if (!drag) return;

        const handleMove = (e) => {
            e.preventDefault();
            const ev = e.touches ? e.touches[0] : e;
            const rect = clockRef.current?.getBoundingClientRect();
            if (!rect) return;
            const scalingFactor = 2 * C / rect.width;
            const angle = Math.atan2(
                (ev.clientY - rect.top) * scalingFactor - C,
                (ev.clientX - rect.left) * scalingFactor - C
            );
            const minutes = radiansToMinutes(angle);
            dispatch({ type: drag === "start" ? "setStart" : "setEnd", minutes });
        };

        const onUp = () => {
            setDrag(null);
            setTimeString(`${formatMinutes(timeRef.current.start)}-${formatMinutes(timeRef.current.end)}`);
        };

        window.addEventListener("pointermove", handleMove);
        window.addEventListener("pointerup", onUp);
        window.addEventListener("touchmove", handleMove, { passive: false });
        window.addEventListener("touchend", onUp);
        return () => {
            window.removeEventListener("pointermove", handleMove);
            window.removeEventListener("pointerup", onUp);
            window.removeEventListener("touchmove", handleMove);
            window.removeEventListener("touchend", onUp);
        };
    }, [drag, C]);

    const startAngle = minutesToRadians(time.start);
    const endAngle = minutesToRadians(time.end);
    const startPos = polarToCartesian(HAND_LEN, startAngle);
    const endPos = polarToCartesian(HAND_LEN, endAngle);

    const isStartError = !isValid12HourTime(startText);
    const isEndError = !isValid12HourTime(endText);

    return (
        <Container>
            <TimeInputContainer>
                <div style={{ display: "flex", alignItems: "center", gap: "4px"}}>
                   <div style={{ display: "flex", flexDirection: "column", alignItems: "center"}}>
                        <span style={{fontSize: '12px'}}>Start</span>
                        <TimeInput 
                            type="text" 
                            value={startText} 
                            $isError={isStartError}
                            onChange={(e) => {handleTimeInputChange(e, setStartText)}}
                            onBlur={(e) => {
                                const fixedValue = fixTimeInputOnBlur(e.target.value);
                                setStartText(fixedValue);
                                if (isValid12HourTime(fixedValue)) {
                                    dispatch({ type: "setStart", minutes: ampmTimeToMinutes(fixedValue, startAMPM) });
                                    const newTime = `${formatMinutes(ampmTimeToMinutes(fixedValue, startAMPM))}-${formatMinutes(time.end)}`;
                                    if (newTime !== timeString) {
                                        setTimeString(newTime);
                                    }
                                } else {
                                    setStartText(formatMinutesForDisplay(time.start).time);
                                }
                            }} 
                        />
                    </div> 
                    <CustomDropdown
                        style={{width: "60px", marginTop: "18px"}}
                        options={['AM', 'PM']}
                        value={startAMPM}
                        onChange={(option) => {
                            dispatch({ type: "setStart", minutes: ampmTimeToMinutes(formatMinutesForDisplay(time.start).time, option) });
                            setTimeString(`${formatMinutes(ampmTimeToMinutes(formatMinutesForDisplay(time.start).time, option))}-${formatMinutes(time.end)}`);
                        }}
                    />
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px"}}>
                   <div style={{ display: "flex", flexDirection: "column", alignItems: "center"}}>
                        <span style={{fontSize: '12px'}}>End</span>
                        <TimeInput 
                            type="text" 
                            value={endText} 
                            $isError={isEndError}
                            onChange={(e) => {handleTimeInputChange(e, setEndText)}}
                            onBlur={(e) => {
                                const fixedValue = fixTimeInputOnBlur(e.target.value);
                                setEndText(fixedValue);
                                if (isValid12HourTime(fixedValue)) {
                                    dispatch({ type: "setEnd", minutes: ampmTimeToMinutes(fixedValue, endAMPM) });
                                    const newTime = `${formatMinutes(time.start)}-${formatMinutes(ampmTimeToMinutes(fixedValue, endAMPM))}`
                                    if (newTime !== timeString) {
                                        setTimeString(newTime);
                                    }
                                } else {
                                    setEndText(formatMinutesForDisplay(time.end).time);
                                }
                            }} 
                        />
                    </div> 
                    <CustomDropdown
                        style={{width: "60px", marginTop: "18px"}}
                        options={['AM', 'PM']}
                        value={endAMPM}
                        onChange={(option) => {
                            dispatch({ type: "setEnd", minutes: ampmTimeToMinutes(formatMinutesForDisplay(time.end).time, option) });
                            setTimeString(`${formatMinutes(time.start)}-${formatMinutes(ampmTimeToMinutes(formatMinutesForDisplay(time.end).time, option))}`);
                        }}
                    />
                </div>
            </TimeInputContainer>
            <ClockFace 
                ref={clockRef} 
                viewBox={`0 0 ${diameter + viewBoxOffset} ${diameter + viewBoxOffset}`} 
                drag={drag}
                style={{ maxWidth: diameter + viewBoxOffset }}
            >
                {/* Circle */}
                <circle cx={C} cy={C} r={R} fill="none" stroke="#e0e0e0" strokeWidth="1.5" />

                {/* 12 small ticks */}
                {Array.from({ length: 12 }, (_, i) => {
                    const angle = ((i / 12) * 360 - 90) * (Math.PI / 180);
                    const outer = polarToCartesian(R - 1, angle);
                    const inner = polarToCartesian(R - (i % 3 === 0 ? 10 : 6), angle);
                    return (
                        <line
                            key={i}
                            x1={outer.x}
                            y1={outer.y}
                            x2={inner.x}
                            y2={inner.y}
                            stroke={i % 3 === 0 ? "#bdbdbd" : "#e0e0e0"}
                            strokeWidth={i % 3 === 0 ? 1.5 : 1}
                            strokeLinecap="round"
                        />
                    );
                })}

                {/* Time labels */}
                {['12 AM', '6 AM', '12 PM', '6 PM'].map((label, i) => {
                    const angle = ((i * 3 / 12) * 360 - 90) * (Math.PI / 180);
                    const pos = polarToCartesian(R + 20, angle); // R + 15 pushes the text outside the dial
                    return (
                        <text
                            key={label}
                            x={pos.x}
                            y={pos.y}
                            fill="#8c8c8c"
                            fontSize="11px"
                            fontWeight="500"
                            fontFamily="'SFPro', sans-serif"
                            textAnchor="middle"
                            dominantBaseline="central"
                        >
                            {label}
                        </text>
                    );
                })}

                {/* Highlighted wedge */}
                <path d={arcPath(startAngle, endAngle)} fill="rgba(174, 174, 184, 0.2)" />

                {/* Start hand */}
                <line x1={C} y1={C} x2={startPos.x} y2={startPos.y} stroke="#3E3E40" strokeWidth="2" strokeLinecap="round" />

                {/* End hand */}
                <line x1={C} y1={C} x2={endPos.x} y2={endPos.y} stroke="#3E3E40" strokeWidth="2" strokeLinecap="round" />

                {/* Center dot */}
                <circle cx={C} cy={C} r="4" fill="#3E3E40" />

                {/* Start knob */}
                <g 
                    onPointerDown={(e) => { e.preventDefault(); e.stopPropagation(); setDrag("start"); }} style={{ cursor: "grab" }}
                    onPointerUp={() => { console.log("up"); }}
                >
                    <circle cx={startPos.x} cy={startPos.y} r={KNOB + 10} fill="transparent" />
                    <circle cx={startPos.x} cy={startPos.y} r={KNOB} fill="#3E3E40" />
                    {drag === "start" && <circle cx={startPos.x} cy={startPos.y} r={KNOB + 8} fill="rgba(174, 174, 184,0.2)" />}
                </g>

                {/* End knob */}
                <g onPointerDown={(e) => { e.preventDefault(); e.stopPropagation(); setDrag("end"); }} style={{ cursor: "grab" }}>
                    <circle cx={endPos.x} cy={endPos.y} r={KNOB + 10} fill="transparent" />
                    <circle cx={endPos.x} cy={endPos.y} r={KNOB} fill="#3E3E40" />
                    {drag === "end" && <circle cx={endPos.x} cy={endPos.y} r={KNOB + 8} fill="rgba(174, 174, 184,0.2)" />}
                </g>
            </ClockFace>
        </Container>
    )
}

export default TimeSelect;