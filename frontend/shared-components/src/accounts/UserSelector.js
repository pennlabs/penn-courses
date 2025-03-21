import React, { useState } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import { useOnClickOutside } from "../useOnClickOutside";

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
    background: ${(props) => {
        if (props.$color === "purple") {
            return props.$selected ? "#6B73D0" : "#c8cbed";
        }
        return props.$selected ? "#9a9a9a" : "#656565";
    }};
    &:hover {
        background: ${(props) =>
            props.$color === "purple" ? "#9399DB" : "#444444"};
    }
`;

const InnerMenu = styled.div`
    background: white;
    color: #4a4a4a;
    border-radius: 4px;
    position: relative;
    padding: 0.32rem;
    font-size: 0.85rem;
    box-shadow: 0 0 5px 0 lightgrey;
    right: ${(props) => (props.$leftAligned ? "0%" : "61%")};
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

const TriangleUp = styled.div`
    transform: ${({ down }) => (down ? "rotate(180deg)" : "rotate(0)")};
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 10px solid white;
    position: relative;
    left: 11%;
    transition: 200ms ease border;
    z-index: 5;
`;

const LogoutDropdownContainer = styled.div`
    min-width: 7rem !important;
    vertical-align: center;
`;

const LogoutDropdownMenu = styled.div`
    min-width: 7rem !important;
    margin-top: 0;
    display: ${({ selected }) => (selected ? "block" : "none")};
    left: 0;
    min-width: 12rem;
    ${({ floattop }) =>
        floattop ? "padding-bottom: 4px" : "padding-top: 4px"};
    position: absolute;
    ${({ floattop }) => (floattop ? "bottom: 100%" : "top: 100%")};
    z-index: 20;
`;

const LogoutIconContainer = styled.div`
    height: 100%;
    float: right;
    margin-right: 0.45rem;
`;

const Dropdown = styled.div`
    display: inline-flex;
    position: relative;
    vertical-align: top;
`;

const UserSelector = ({
    user: { username, ...rest },
    onLogout,
    leftAligned,
    backgroundColor,
    nameLength,
    dropdownTop, // whether the dropdown menu should appear above or below
}) => {
    const [selected, setSelected] = useState(false);

    const firstName = rest.first_name;
    const lastName = rest.last_name;

    const onClickOutside = useOnClickOutside(() => {
        setSelected(false);
    }, !selected);

    return (
        <Dropdown ref={onClickOutside}>
            <NameBubble
                $selected={selected}
                $color={backgroundColor}
                role="button"
                id="user-selector"
                onClick={() => setSelected(!selected)}
            >
                <span>
                    {" "}
                    {(firstName && firstName.substring(0, nameLength || 1)) ||
                        "U"}{" "}
                </span>
            </NameBubble>
            <LogoutDropdownMenu
                selected={selected}
                floattop={dropdownTop.toString()}
            >
                <LogoutDropdownContainer className="dropdown-menu-container">
                    <TriangleUp down={dropdownTop.toString()} />
                    <InnerMenu $leftAligned={leftAligned}>
                        <NameContainer>
                            {" "}
                            {firstName} {lastName}{" "}
                        </NameContainer>
                        <EmailContainer> {username} </EmailContainer>
                        <LogoutButton
                            role="button"
                            onClick={() => {
                                fetch("/accounts/logout/", {
                                    method: "GET",
                                    redirect: "follow",
                                }).then(onLogout);
                            }}
                        >
                            Logout
                            <LogoutIconContainer>
                                <i className="fas fa-sign-out-alt" />
                            </LogoutIconContainer>
                        </LogoutButton>
                    </InnerMenu>
                </LogoutDropdownContainer>
            </LogoutDropdownMenu>
        </Dropdown>
    );
};

UserSelector.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    onLogout: PropTypes.func,
    leftAligned: PropTypes.bool,
    backgroundColor: PropTypes.string,
    nameLength: PropTypes.number,
    dropdownTop: PropTypes.bool,
};

export default UserSelector;
