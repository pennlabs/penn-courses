import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";
import {
    fetchFriendships,
    rejectFriendRequest,
} from "../../actions/friendshipUtil";
import { User, Friendship, Schedule as ScheduleType } from "../../types";
import { nextAvailable } from "../../actions";

interface FriendButtonProps {
    friendName: string;
    display: () => void;
    removeFriend: () => void;
}

const FriendButton = ({
    friendName,
    display,
    removeFriend,
}: FriendButtonProps) => (
    <div>
        <div>{friendName}</div>
        <button onClick={display}>Display</button>
        <button onClick={removeFriend}>Remove</button>
    </div>
);

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
        background: #ebedf1;
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

const ScheduleOptionsContainer = styled.div<{ isPrimary: boolean }>`
    display: flex;
    flex-grow: 0.5;
    justify-content: flex-end;
    width: 25%;

    i {
        pointer-events: auto;
        color: #b2b2b2;
    }

    i:hover {
        color: #7E7E7E; !important;
    }

    i.active {
        color: ${(props) => (props.isPrimary ? "#669afb" : "#b2b2b2")};
    }

    i.active:hover {
        color: ${(props) =>
            props.isPrimary ? "#669afb" : "#7E7E7E"}; !important
    }
`;

interface DropdownButton {
    isActive: boolean;
    isPrimary: boolean;
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

const DropdownButton = ({
    isActive,
    isPrimary,
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
            if (targetClass && targetClass?.indexOf("option-content") !== -1) {
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
        <ScheduleOptionsContainer isPrimary={isPrimary}>
            {hasFriends && (
                <Icon
                    className="option-content"
                    onClick={setPrimary}
                    role="button"
                >
                    <i
                        className={`active ${
                            isPrimary ? "fa" : "far"
                        } fa-user option-content`}
                        aria-hidden="true"
                    />
                </Icon>
            )}
            <Icon className="option-content" onClick={rename} role="button">
                <i className="far fa-edit option-content" aria-hidden="true" />
            </Icon>
            <Icon className="option-content" onClick={copy} role="button">
                <i className="far fa-copy option-content" aria-hidden="true" />
            </Icon>
            <Icon className="option-content" onClick={remove} role="button">
                <i className="fa fa-trash option-content" aria-hidden="true" />
            </Icon>
        </ScheduleOptionsContainer>
    </DropdownButtonContainer>
);

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
        background: #ebedf1;
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
    background-color: #fff;

    &:hover {
        background-color: #dfe9fc;
    }

    span {
        float: left;
        text-align: left;
        color: #4a4a4a;
    }

    div {
        background-color: #e58d8d;
        border-radius: 0.5rem;
        padding: 0 0.3rem 0 0.3rem;
        color: white;
        font-size: 0.68rem;
        align-items: center;
    }
`;

interface ScheduleSelectorDropdownProps {
    user: User;
    activeName: string;
    primaryScheduleId: string;
    displayState: string;
    allSchedules: ScheduleType[];
    displayOwnSchedule: (scheduleName: string) => void;
    displayFriendSchedule: (username: string) => void;
    mutators: {
        copy: (scheduleName: string) => void;
        remove: (user: User, scheduleName: string, scheduleId: string) => void;
        rename: (oldName: string) => void;
        createSchedule: () => void;
        addFriend: () => void;
        showRequests: () => void;
        setPrimary: (user: User, scheduleName: string) => void;
    };
}

const ScheduleSelectorDropdown = ({
    user,
    activeName,
    primaryScheduleId,
    displayState,
    allSchedules,
    displayOwnSchedule,
    displayFriendSchedule,
    mutators: {
        copy,
        remove,
        rename,
        createSchedule,
        addFriend,
        showRequests,
        setPrimary,
    },
}: ScheduleSelectorDropdownProps) => {
    const [isActive, setIsActive] = useState(false);
    const ref = useRef<HTMLDivElement>(null);
    const [hasFriends, setHasFriends] = useState(false);
    const [numRequests, setNumRequests] = useState(0);
    const [friendshipData, setFriendshipData] = useState<{
        received: Friendship[];
        sent: Friendship[];
        friends: User[];
    }>();

    useEffect(() => {
        setHasFriends(friendshipData?.friends.length != 0);
        setNumRequests(
            friendshipData?.received ? friendshipData.received.length : 0
        );
    }, [friendshipData]);

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
            <span className="selected_name">
                {displayState !== "Self" && displayState !== "Not Found"
                    ? displayState
                    : activeName}
            </span>
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
                    {allSchedules &&
                        Object.entries(allSchedules).map(([name, data]) => {
                            return (
                                <DropdownButton
                                    key={data.id}
                                    isActive={name === activeName}
                                    makeActive={() => {
                                        setIsActive(false);
                                    }}
                                    isPrimary={primaryScheduleId === data.id}
                                    hasFriends={hasFriends}
                                    onClick={() => displayOwnSchedule(name)}
                                    text={name}
                                    mutators={{
                                        setPrimary: () => {
                                            setPrimary(user, data.id);
                                        },
                                        copy: () =>
                                            copy(
                                                nextAvailable(
                                                    name,
                                                    allSchedules
                                                )
                                            ),
                                        remove: () =>
                                            remove(user, name, data.id),
                                        rename: () => rename(name),
                                    }}
                                />
                            );
                        })}
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
                                    {primaryScheduleId === "-1" ? (
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
                        {friendshipData?.friends?.map((friend) => (
                            <FriendButton
                                friendName={`${friend.first_name} ${friend.last_name}`}
                                display={() =>
                                    displayFriendSchedule(friend.username)
                                }
                                removeFriend={() => {
                                    rejectFriendRequest(friend.username);
                                    fetchFriendships(setFriendshipData, user);
                                }}
                            />
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
                            <span> Pending Requests </span>
                            <div>{numRequests}</div>
                        </PendingRequests>
                    </FriendContent>
                </DropdownContent>
            </DropdownMenu>
        </ScheduleDropdownContainer>
    );
};

export default ScheduleSelectorDropdown;
