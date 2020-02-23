import React from "react";
import PropTypes from "prop-types";
import { isMobile } from "react-device-detect";

export default function Block(props) {
    const days = ["M", "T", "W", "R", "F", "S", "U"];
    const {
        offsets, meeting, course, remove, style, focusSection,
    } = props;
    const { day, start, end } = meeting;
    const { id, color, coreqFulfilled } = course;
    const pos = {
        gridRowStart: (start - offsets.time) * 2 + offsets.row + 1,
        gridRowEnd: (end - offsets.time) * 2 + offsets.col + 1,
        gridColumn: days.indexOf(day) + 1 + offsets.col,
    };
    return (
        <div style={{ ...pos }}>
            <div
                role="button"
                className={`block ${color}`}
                style={{ ...style, position: "relative", height: "100%" }}
                onClick={focusSection}
            >
                <div className="inner-block">
                    {!isMobile && (
                        <span
                            role="button"
                            className="remove"
                            onClick={(e) => {
                                remove();
                                e.stopPropagation();
                            }}
                        >
                            <i className="fas fa-times" />
                        </span>
                    )
                    }
                    <span
                        className={coreqFulfilled ? "hide" : ""}
                        title="Registration is required for an associated section."
                    >
                        <i className="fas fa-exclamation warning" />
                    </span>
                    <span>{id.replace(/-/g, " ")}</span>
                </div>
            </div>
        </div>

    );
}

Block.propTypes = {
    offsets: PropTypes.shape({
        time: PropTypes.number,
        row: PropTypes.number,
        col: PropTypes.number,
    }),
    meeting: PropTypes.shape({
        day: PropTypes.string,
        start: PropTypes.number,
        end: PropTypes.number,
    }),
    course: PropTypes.shape({
        id: PropTypes.string,
        color: PropTypes.string,
        coreqFulfilled: PropTypes.bool,
    }),
    remove: PropTypes.func,
    style: PropTypes.shape({
        width: PropTypes.string,
        left: PropTypes.string,
    }),
    focusSection: PropTypes.func,
};
