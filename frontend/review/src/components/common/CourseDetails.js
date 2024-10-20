import React from "react";

const getTimeString = meetings => {
  const intToTime = t => {
    let hour = Math.floor(t % 12);
    let min = Math.round((t % 1) * 100);
    if (hour === 0) {
      hour = 12;
    }
    let minStr = min === 0 ? "00" : min.toString();
    return `${hour}:${minStr}`;
  };

  if (!meetings || meetings.length === 0) {
    return "TBA";
  }
  const times = {};
  let maxcount = 0;
  let maxrange = "";
  meetings.forEach(meeting => {
    const rangeId = `${meeting.start}-${meeting.end}`;
    if (!times[rangeId]) {
      times[rangeId] = [meeting.day];
    } else {
      times[rangeId].push(meeting.day);
    }
    if (times[rangeId].length > maxcount) {
      maxcount = times[rangeId].length;
      maxrange = rangeId;
    }
  });

  let daySet = "";
  "MTWRFSU".split("").forEach(day => {
    times[maxrange].forEach(d => {
      if (d === day) {
        daySet += day;
      }
    });
  });

  return `${intToTime(parseFloat(maxrange.split("-")[0]))}-${intToTime(
    parseFloat(maxrange.split("-")[1])
  )} ${daySet}`;
};

export const CourseDetails = ({ data = {} }) => {
  const { id, status, meetings } = data;
  const isOpen = status === "O";
  return (
    <li>
      {id}
      <i className={`ml-2 fa fa-fw fa-${isOpen ? "check" : "times"}`} />
      <span className="ml-2" style={{ color: "#aaa" }}>
        {getTimeString(meetings)}
      </span>
    </li>
  );
};
