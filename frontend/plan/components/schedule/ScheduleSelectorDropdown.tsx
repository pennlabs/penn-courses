import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";
import { fetchFriendships } from "../../actions/friendshipUtil";
import { User, Friendship } from "../../types";

interface DropdownButton {
    isActive: boolean;
    text: string;
    hasFriends: boolean;
    onClick: () => void;
    makeActive: () => void;
    mutators: {
        setPrimary: () => void;
        copy: () => void;
        remove: () => void;
        rename: () => void;
    };
}

const DropdownButtonContainer = styled.div<{ isActive: boolean }>`
    line-height: 1.5;
    position: relative;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 1rem;
    transition: background 0.1s ease;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    background: ${(props) => (props.isActive ? "#F5F6F8" : "#FFF")};

    &:hover {
        background: ${(props) => (props.isActive ? "#EBEDF1" : "#F5F6F8")};
    }

    * {
        font-size: 0.75rem;
        color: #333333;
    }
`;

const ScheduleNameContainer = styled.div`
    display: flex;
    flex-grow: 1;
    font-weight: 400;
    max-width: 50%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
`;

const ScheduleOptionsContainer = styled.div`
    display: flex;
    flex-grow: 0.5;
    justify-content: flex-end;
    width: 25%;

    i {
        color: #b2b2b2 !important;
    }

    i:hover {
        color: #f5f6f8 !important;
    }
`;

const DropdownButton = ({
    isActive,
    text,
    hasFriends,
    onClick,
    makeActive,
    mutators: { setPrimary, copy, remove, rename },
}: DropdownButton) => (
    <DropdownButtonContainer
        role="button"
        onClick={(e) => {
            // NOTE: explicit cast to HTMLElement to resolve compile error
            // .getAttribute doesn't exist on type EventTarget
            const targetClass = (e.target as HTMLElement).getAttribute("class");
            if (targetClass && targetClass.indexOf("s-option") !== -1) {
                // one of the icons has been clicked
                return;
            }
            if (onClick) {
                onClick();
            }
            if (makeActive) {
                makeActive();
            }
        }}
        isActive={isActive}
    >
        <ScheduleNameContainer>{text}</ScheduleNameContainer>
        <ScheduleOptionsContainer>
            {hasFriends && (
                <div
                    onClick={setPrimary}
                    className="s-option-copy"
                    role="button"
                >
                    <Icon>
                        <i className="far fa-user" aria-hidden="true" />
                    </Icon>
                </div>
            )}
            <div onClick={rename} className="s-option-copy" role="button">
                <Icon>
                    <i className="far fa-edit" aria-hidden="true" />
                </Icon>
            </div>
            <div onClick={copy} className="s-option-copy" role="button">
                <Icon>
                    <i className="far fa-copy" aria-hidden="true" />
                </Icon>
            </div>
            <div onClick={remove} className="s-option-copy" role="button">
                <Icon>
                    <i className="fa fa-trash" aria-hidden="true" />
                </Icon>
            </div>
        </ScheduleOptionsContainer>
    </DropdownButtonContainer>
);

interface ScheduleSelectorDropdownProps {
    activeName: string;
    content: {
        text: string;
        onClick: () => void;
    }[];
    user: User;
    mutators: {
        setPrimary: (scheduleName: string) => void;
        copy: (scheduleName: string) => void;
        remove: (scheduleName: string) => void;
        rename: (oldName: string) => void;
        createSchedule: () => void;
        addFriend: () => void;
        showRequests: () => void;
    };
}

const ScheduleDropdownContainer = styled.div`
    border-radius: 0.5rem;
    border: 0;
    outline: none;
    display: inline-flex;
    position: relative;
    vertical-align: top;

    * {
        border: 0;
        outline: none;
    }

    i.fa.fa-chevron-down::before {
        content: ${({ isActive }: { isActive: boolean }) =>
            isActive ? '"\f077"' : ""} !important;
    }
`;

const DropdownTrigger = styled.div`
    margin-left: 0.75rem;
    height: 1.5rem;
    width: 1.5rem;
    text-align: center;
    outline: none !important;
    border: none !important;
    background: transparent;

    div {
        background: ${({ isActive }: { isActive: boolean }) =>
            isActive ? "rgba(162, 180, 237, 0.38) !important" : "none"};
    }

    div:hover {
        background: rgba(175, 194, 255, 0.27);
    }
`;

const DropdownMenu = styled.div`
    margin-top: 0.1rem !important;
    display: ${({ isActive }: { isActive: boolean }) =>
        isActive ? "block" : "none"};
    left: 0;
    min-width: 12rem;
    padding-top: 4px;
    position: absolute;
    top: 100%;
    z-index: 20;
`;

const DropdownContent = styled.div`
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
    padding: 0;
`;

const FriendContent = styled.div`
    background-color: #fff;
    border-top: 0.05rem solid #c7c6ce;
    padding: 0;

    div.info {
        font-weight: 450;
        padding: 0.25rem 0.75rem;
        font-size: 0.5rem;
        opacity: 75%;
    }
    div i {
        color: #669afb;
    }

    .share-with {
        font-size: 0.68rem;
        color: #171717;
        font-weight: 700;
    }
`;

const AddNew = styled.a`
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    font-size: 0.75rem;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 1rem;
    transition: background 0.1s ease;
    background: #fff;

    &:hover {
        background: #f5f6f8;
    }

    span,
    span i {
        float: left;
        text-align: left;
        color: #669afb !important;
    }
`;

const PendingRequests = styled.a`
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    font-size: 0.68rem;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 0.75rem;
    transition: background 0.1s ease;
    background: #fff;

    &:hover {
        background: #f5f6f8;
    }

    span {
        float: left;
        text-align: left;
        color: #4a4a4a;
    }

    div {
        background-color: #e58d8d;
        border-radius: 0.5rem;
        padding: 0.05rem 0.3rem 0 0.3rem;
        color: white;
        font-size: 0.6rem;
    }
`;

const ScheduleSelectorDropdown = ({
    activeName,
    content,
    user,
    mutators: {
        setPrimary,
        copy,
        remove,
        rename,
        createSchedule,
        addFriend,
        showRequests,
    },
}: ScheduleSelectorDropdownProps) => {
    const [isActive, setIsActive] = useState(false);
    const ref = useRef<HTMLDivElement>(null);
    const [hasFriends, setHasFriends] = useState(false);
    const [numRequests, setNumRequests] = useState(2);
    const [primarySelected, setPrimarySelected] = useState(false);
    const [friendshipData, setFriendshipData] = useState<{
        received: Friendship[];
        sent: Friendship[];
        accepted: Friendship[];
    }>();
    const [dataChanged, setDataChanged] = useState(false);

    useEffect(() => {
        const listener = (event: Event) => {
            if (
                ref.current &&
                !ref.current.contains(event.target as HTMLElement)
            ) {
                setIsActive(false);
            }
        };
        document.addEventListener("click", listener);
        return () => {
            document.removeEventListener("click", listener);
        };
    });

    return (
        <ScheduleDropdownContainer ref={ref} isActive={isActive}>
            <span className="selected_name">{activeName}</span>
            <DropdownTrigger
                isActive={isActive}
                onClick={() => {
                    fetchFriendships(setFriendshipData, user);
                    setIsActive(!isActive);
                }}
                role="button"
            >
                <div aria-haspopup={true} aria-controls="dropdown-menu">
                    <Icon>
                        <i className="fa fa-chevron-down" aria-hidden="true" />
                    </Icon>
                </div>
            </DropdownTrigger>
            <DropdownMenu isActive={isActive} role="menu">
                <DropdownContent>
                    {Array.from(content.entries()).map(
                        ([index, { onClick, text: scheduleName }]) => (
                            <DropdownButton
                                key={index}
                                isActive={scheduleName === activeName}
                                makeActive={() => {
                                    setIsActive(false);
                                }}
                                hasFriends={hasFriends}
                                onClick={onClick}
                                text={scheduleName}
                                mutators={{
                                    setPrimary: () => setPrimary(scheduleName),
                                    copy: () => copy(scheduleName),
                                    remove: () => remove(scheduleName),
                                    rename: () => rename(scheduleName),
                                }}
                            />
                        )
                    )}
                    <AddNew onClick={createSchedule} role="button" href="#">
                        <Icon>
                            <i className="fa fa-plus" aria-hidden="true" />
                        </Icon>
                        <span> Add new schedule </span>
                    </AddNew>

                    <FriendContent>
                        <div className="info">
                            {hasFriends ? (
                                <div>
                                    {primarySelected ? (
                                        <div className="share-with">
                                            Share With
                                        </div>
                                    ) : (
                                        <div>
                                            Click{" "}
                                            <i
                                                className="fa fa-user"
                                                aria-hidden="true"
                                            />{" "}
                                            to set your shared schedule
                                        </div>
                                    )}
                                </div>
                            ) : (
                                "Add a friend to share a schedule"
                            )}
                        </div>
                        {friendshipData?.accepted?.map((friendObj) => (
                            <div>{friendObj.recipient.first_name}</div>
                        ))}
                        <AddNew onClick={addFriend} role="button" href="#">
                            <Icon>
                                <i className="fa fa-plus" aria-hidden="true" />
                            </Icon>
                            <span> Add new friend </span>
                        </AddNew>
                        <PendingRequests
                            onClick={showRequests}
                            role="button"
                            href="#"
                        >
                            <span> Pending Share Requests </span>
                            <div>{numRequests}</div>
                        </PendingRequests>
                    </FriendContent>
                </DropdownContent>
            </DropdownMenu>
        </ScheduleDropdownContainer>
    );
};

export default ScheduleSelectorDropdown;
