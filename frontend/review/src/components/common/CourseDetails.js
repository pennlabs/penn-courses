import React from 'react'

export const CourseDetails = ({ data = {} }) => {
  const {
    is_closed: isClosed,
    is_cancelled: isCanceled,
    section_id_normalized: sectionId,
    meetings,
  } = data
  const isOpen = !isClosed && !isCanceled
  const meetingDates = meetings.map(
    ({ meeting_days: days, start_time: start, end_time: end }) =>
      `${days} ${start} - ${end}`
  )
  return (
    <li>
      {sectionId}
      <i className={`ml-2 fa fa-fw fa-${isOpen ? 'check' : 'times'}`} />
      <span className="ml-2" style={{ color: '#aaa' }}>
        {meetingDates.join(', ')}
      </span>
    </li>
  )
}
