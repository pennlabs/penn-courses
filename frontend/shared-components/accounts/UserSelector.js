import React, { useState } from "react";
import PropTypes from "prop-types";
import { useOnClickOutside } from "../useOnClickOutside";
import "../styles/accounts.css";
import styled from "styled-components";

const NameBubble = styled.div`
    color: white;
    height: 2.5rem;
    width: 2.5rem;
    text-align: center;
    border-radius: 1.25rem;
    font-size: 1.4rem;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    justify-content: center;
    user-select: none;
    transition: 150ms ease background;
    margin-right: 0.85rem;    
    background: ${
    props => props.color === "purple" ?
        (props.selected ? "#6B73D0" :
            "#c8cbed") :
        (props.selected ? "#9a9a9a" :
            "#656565")} ;
    &:hover {
        background: ${props => props.color === "purple" ? "#9399DB" : "#444444"};
    }
`;

const UserSelector = ({
    user: { username, ...rest }, onLogout,
    onLeft, backgroundColor, nameLength
}) => {
    const [selected, setSelected] = useState(false);

    const firstName = rest.first_name;
    const lastName = rest.last_name;

    const onClickOutside = useOnClickOutside(() => {
        setSelected(false);
    }, !selected);

    return (
        <div
            className={`dropdown${selected ? " is-active" : ""}`}
            ref={onClickOutside}
        >
            <NameBubble
                selected={selected}
                color={backgroundColor}
                className={`dropdown-trigger`}
                role="button"
                id="user-selector"
                onClick={() => setSelected(!selected)}
            >
                <span>
                    {" "}
                    {(firstName && firstName.substring(0, nameLength || 1)) || "U"}
                    {" "}
                </span>
            </NameBubble>
            <div className="logout dropdown-menu">
                <div id="logout-dropdown-menu-container">
                    <div className="triangle-up" />
                    <div id="logout-dropdown-inner-menu" className={`${onLeft ? " on-left" : ""}`}>
                        <p className="name-container">
                            {" "}
                            {firstName}
                            {" "}
                            {lastName}
                            {" "}
                        </p>
                        <p className="email-container">
                            {" "}
                            {username}
                            {" "}
                        </p>
                        <div
                            role="button"
                            id="logout-button"
                            onClick={() => {
                                fetch("/accounts/logout/", {
                                    method: "GET",
                                    redirect: "follow",
                                })
                                    .then(onLogout);
                            }}
                        >
                            Logout
                            <div id="logout-icon-container">
                                <i className="fas fa-sign-out-alt" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

UserSelector.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    onLogout: PropTypes.func,
    onLeft: PropTypes.bool,
};

export default UserSelector;
