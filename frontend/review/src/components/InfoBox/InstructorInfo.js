import React from "react";

export default ({ name, contact, notes }) => (
  <div className="instructor">
    <div className="title">{name}</div>
    {contact && (
      <div>
        <p className="desc">
          Email:{" "}
          <a href={`mailto:${contact.email}`}> {contact.email.toLowerCase()}</a>
        </p>
      </div>
    )}
    {notes &&
      notes.map(note => (
        <div key={note} className="note">
          <i className="fa fa-thumbtack" /> {note}
        </div>
      ))}
  </div>
);
