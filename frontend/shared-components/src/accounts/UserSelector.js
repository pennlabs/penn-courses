import React, { useState } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import { useOnClickOutside } from "../useOnClickOutside";
import "bulma/css/bulma.css";
import "../styles/accounts.css";

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
    (props) => {
        if (props.color === "purple") {
            return props.selected ? "#6B73D0"
                : "#c8cbed";
        }
        return props.selected ? "#9a9a9a"
            : "#656565";
    }};
    &:hover {
        background: ${(props) => (props.color === "purple" ? "#9399DB" : "#444444")};
    };
`;

const InnerMenu = styled.div`
    background: white;
    color: #4a4a4a;
    border-radius: 4px;
    position: relative;
    padding: 0.32rem;
    font-size: 0.85rem;
    box-shadow: 0 0 5px 0 lightgrey;
    right: ${(props) => props.onLeft ? "0%" : "61%"}
`;

const NameContainer = styled.p`
    font-weight: bold;
    margin: 0.5rem;
    font-size: 1.25rem;
`;

const EmailContainer = styled.p`
    font-size: 0.8rem;
    margin: 0.5rem;
    color: #828282;
`;

const LogoutButton = styled.div`
    cursor: pointer;   
    background: white;
    transition: 200ms ease background;
    margin: 0.5rem;
    &:hover {
        background: rgb(245, 245, 245);
    }
`;

const UserSelector = ({
    user: { username, ...rest }, onLogout,
    onLeft, backgroundColor, nameLength,
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
                className="dropdown-trigger"
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
                    <InnerMenu onLeft={onLeft}>
                        <NameContainer>
                            {" "}
                            {firstName}
                            {" "}
                            {lastName}
                            {" "}
                        </NameContainer>
                        <EmailContainer>
                            {" "}
                            {username}
                            {" "}
                        </EmailContainer>
                        <LogoutButton
                            role="button"
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
                        </LogoutButton>
                    </InnerMenu>
                </div>
            </div>
        </div>
    );
};

UserSelector.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    onLogout: PropTypes.func,
    onLeft: PropTypes.bool,
    backgroundColor: PropTypes.string,
    nameLength: PropTypes.number,
};

export default UserSelector;
