import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { changeSortType } from "../../actions";

const DropdownButton = ({ isActive, text, onClick, makeActive }) => (
    <div
        role="button"
        onClick={() => {
            if (onClick) {
                onClick();
            }
            if (makeActive) {
                makeActive();
            }
        }}
        className={`dropdown-item${isActive ? " is-active" : ""}`}
    >
        {text}
    </div>
);

DropdownButton.propTypes = {
    isActive: PropTypes.bool,
    text: PropTypes.string,
    onClick: PropTypes.func,
    makeActive: PropTypes.func,
};

const contents = ["Name", "Quality", "Difficulty", "Good & Easy"];

const SearchSortDropdown = ({ updateSort }) => {
    const [isActive, setIsActive] = useState(false);
    const [activeItem, setActiveItem] = useState(0);
    const [ref, setRef] = useState(null);

    useEffect(() => {
        const listener = (event) => {
            if (ref && !ref.contains(event.target)) {
                setIsActive(false);
            }
        };
        document.addEventListener("click", listener);
        return () => {
            document.removeEventListener("click", listener);
        };
    });
    return (
        <div
            ref={(node) => setRef(node)}
            className={`classic dropdown${isActive ? " is-active" : ""}`}
        >
            <span className="selected_name">Sort by</span>
            <div
                className="classic-dropdown-trigger"
                onClick={() => setIsActive(!isActive)}
                role="button"
            >
                <div aria-haspopup={true} aria-controls="dropdown-menu">
                    <span className="icon is-small">
                        <i className="fa fa-chevron-down" aria-hidden="true" />
                    </span>
                </div>
            </div>
            <div className="dropdown-menu" role="menu">
                <div className="dropdown-content" style={{ width: "6rem" }}>
                    {Array.from(contents.entries()).map(([index, sortType]) => (
                        <DropdownButton
                            key={index}
                            isActive={activeItem === index}
                            makeActive={() => {
                                setActiveItem(index);
                                setIsActive(false);
                            }}
                            onClick={() => updateSort(sortType)}
                            text={sortType}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

SearchSortDropdown.propTypes = {
    updateSort: PropTypes.func,
};

const mapStateToProps = () => ({});
const mapDispatchToProps = (dispatch) => ({
    updateSort: (sortMode) => dispatch(changeSortType(sortMode)),
});

export default connect(mapStateToProps, mapDispatchToProps)(SearchSortDropdown);
