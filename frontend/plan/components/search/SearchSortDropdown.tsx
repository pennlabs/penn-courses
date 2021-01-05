import React, { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { changeSortType } from "../../actions";

interface DropDownButtonProps {
    isActive: boolean;
    text: string;
    onClick: () => void;
    makeActive: () => void;
}
const DropdownButton = ({
    isActive,
    text,
    onClick,
    makeActive,
}: DropDownButtonProps) => (
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

type SortByType = "Name" | "Quality" | "Difficulty" | "Good & Easy";
const contents: SortByType[] = ["Name", "Quality", "Difficulty", "Good & Easy"];

const SearchSortDropdown = (obj: { updateSort: (s: SortByType) => void }) => {
    const [isActive, setIsActive] = useState(false);
    const [activeItem, setActiveItem] = useState(0);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const listener = (event: MouseEvent) => {
            // Cast is unavoidable https://github.com/Microsoft/TypeScript/issues/15394#issuecomment-297495746
            if (ref.current && !ref.current.contains(event.target as Node)) {
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
            ref={ref}
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
                    {contents.map((sortType, index) => (
                        <DropdownButton
                            key={index}
                            isActive={activeItem === index}
                            makeActive={() => {
                                setActiveItem(index);
                                setIsActive(false);
                            }}
                            onClick={() => obj.updateSort(sortType)}
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
//@ts-ignore
const mapDispatchToProps = dispatch => ({
    //@ts-ignore
    updateSort: sortMode => dispatch(changeSortType(sortMode)),
});

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(SearchSortDropdown);
