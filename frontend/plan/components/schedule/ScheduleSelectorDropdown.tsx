import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";
import {
    User,
    Schedule as ScheduleType,
    Color,
    FriendshipState,
    Section,
} from "../../types";
import { nextAvailable } from "../../reducers/schedule";
import { PATH_REGISTRATION_SCHEDULE_NAME } from "../../constants/constants";

const ButtonContainer = styled.div<{
    $isActive: boolean;
    $isPrimary?: boolean;
}>`
    line-height: 1.5;
    position: relative;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 0.75rem;
    transition: background 0.1s ease;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    background: ${(props) => (props.$isActive ? "#F5F6F8" : "#FFF")};
    align-items: center;

    &:hover {
        background: #ebedf1;
    }

    * {
        font-size: 0.75rem;
        color: #333333;
    }

    .option-icon i {
        pointer-events: auto;
        color: #b2b2b2;
    }

    .option-icon i:hover {
        color: #7E7E7E; !important;
    }

    .option-icon i.primary {
        color: ${(props) => (props.$isPrimary ? "#669afb" : "#b2b2b2")};
    }

    .option-icon i.primary:hover {
        color: ${(props) =>
            props.$isPrimary ? "#295FCE" : "#7E7E7E"}; !important;
    }

    .initial-icon {
        color: white; !important;
        font-size: 1vw;
    }
`;

const ButtonLabelContainer = styled.div<{ $width: number }>`
    display: flex;
    flex-grow: 1;
    font-weight: 400;
    justify-content: start;
    max-width: ${(props) => props.$width}%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
`;

const InitialIcon = styled.div<{ $color: Color }>`
    color: white;
    background-color: ${(props) => props.$color};
    opacity: 65%;
    justify-content: center;
    align-items: center;
    text-align: center;
    justify-content: center;
    border-radius: 50%;
    font-weight: 600;
    font-size: 1vw;

    display: inline-flex;
    height: 1.75vw;
    max-width: 1.75vw;
    min-width: 1.75vw;
`;

interface FriendButtonProps {
    friendName: string;
    isActive: boolean;
    display: () => void;
    removeFriend: () => void;
    color: Color;
}

const FriendButton = ({
    friendName,
    isActive,
    display,
    removeFriend,
    color,
}: FriendButtonProps) => (
    <ButtonContainer $isActive={isActive} onClick={display}>
        <InitialIcon $color={color}>
            <div className="initial-icon">{friendName.split(" ")[0][0]}</div>
        </InitialIcon>
        <ButtonLabelContainer $width={65}>{friendName}</ButtonLabelContainer>
        <Icon
            onClick={(e) => {
                removeFriend();
                e.stopPropagation();
            }}
            role="button"
            className="option-icon"
        >
            <i className="fa fa-minus-circle" aria-hidden="true" />
        </Icon>
    </ButtonContainer>
);

const ScheduleOptionsContainer = styled.div`
    display: flex;
    flex-grow: 0.5;
    justify-content: flex-end;
    width: 25%;
`;

interface DropdownButton {
    allSchedules: { [name: string]: ScheduleType };
    isActive: boolean;
    isPrimary: boolean;
    text: string;
    hasFriends: boolean;
    onClick: () => void;
    makeActive: () => void;
    mutators: {
        setPrimary: () => void;
        copy: () => void;
        remove: (() => void) | null;
        rename: (() => void) | null;
    };
}

const DropdownButton = ({
    allSchedules,
    isActive,
    isPrimary,
    text,
    hasFriends,
    onClick,
    makeActive,
    mutators: { setPrimary, copy, remove, rename },
}: DropdownButton) => (
    <ButtonContainer
        role="button"
        onClick={() => {
            if (onClick) {
                onClick();
            }
            if (makeActive) {
                makeActive();
            }
        }}
        $isActive={isActive}
        $isPrimary={isPrimary}
    >
        <ButtonLabelContainer $width={50}>{text}</ButtonLabelContainer>
        <ScheduleOptionsContainer>
            {hasFriends && (
                <Icon
                    onClick={(e) => {
                        setPrimary();
                        e.stopPropagation();
                    }}
                    role="button"
                    className="option-icon"
                >
                    <i
                        className={`primary ${
                            isPrimary ? "fa" : "far"
                        } fa-user`}
                        aria-hidden="true"
                    />
                </Icon>
            )}
            {rename && (
                <Icon
                    onClick={(e) => {
                        rename();
                        e.stopPropagation();
                    }}
                    role="button"
                    className="option-icon"
                >
                    <i className="far fa-edit" aria-hidden="true" />
                </Icon>
            )}
            <Icon
                onClick={(e) => {
                    copy();
                    e.stopPropagation();
                }}
                role="button"
                className="option-icon"
            >
                <i className="far fa-copy" aria-hidden="true" />
            </Icon>
            <Icon role="button" className="option-icon">
                <a
                    href={
                        allSchedules[text]
                            ? `/api/plan/${allSchedules[text].id}/calendar/`
                            : undefined
                    }
                    onClick={(e) => e.stopPropagation()}
                    download
                >
                    <i className="fa fa-download" aria-hidden="true" />
                </a>
            </Icon>
            {remove && (
                <Icon
                    onClick={(e) => {
                        remove();
                        e.stopPropagation();
                    }}
                    role="button"
                    className="option-icon"
                >
                    <i className="fa fa-trash" aria-hidden="true" />
                </Icon>
            )}
        </ScheduleOptionsContainer>
    </ButtonContainer>
);

const ScheduleDropdownContainer = styled.div`
    border-radius: 0.5rem;
    border: 0;
    outline: none;
    display: inline-flex;
    position: relative;
    vertical-align: top;
    width: 100%;

    * {
        border: 0;
        outline: none;
    }
`;

const DropdownTrigger = styled.div`
    margin-left: 1.5rem;
    height: 1.5rem;
    width: 1.5rem;
    text-align: center;
    outline: none !important;
    border: none !important;
    background: transparent;
`;

const DropdownMenu = styled.div<{ $isActive: boolean }>`
    margin-top: 0.1rem !important;
    display: ${({ $isActive }) => ($isActive ? "block" : "none")};
    left: 0;
    min-width: 15rem;
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

    .friends {
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
`;

const PendingRequestsNum = styled.div`
    background-color: #e58d8d;
    border-radius: 0.5rem;
    padding: 0 0.3rem 0 0.3rem;
    color: white;
    font-size: 0.68rem;
    align-items: center;
`;

const ScheduleDropdownHeader = styled.div`
    display: flex;
    position: relative;
    width: 100%;
`;

const DownloadSchedulePromoContainer = styled.div`
    display: flex;
    margin-left: auto;
    align-items: center;
`;

const DownloadSchedulePromo = styled.a`
    display: flex;
    gap: 4px;
    border-radius: 0.81rem;
    background-color: #878ed8;
    color: white;
    font-size: 0.75rem;
    align-items: center;
    justify-items: center;
    font-weight: 500;
    justify-content: start;
    padding: 0.25rem 0.6rem;
    user-select: none;
    margin-left: 0.5rem;
    transition: background 0.15s ease;

    &:hover {
        background-color: #767ac2ff;
        color: white;
        cursor: pointer;
    }
`;

const DownloadScheduleInfo = styled.a`
    color: #c4c7eeff;
    transition: background 0.15s ease;

    &:hover {
        color: #b3b5e1ff;
        cursor: pointer;
    }
`;

const ReceivedRequestNotice = styled.div`
    background-color: #e58d8d;
    border-radius: 50%;
    align-items: center;
    width: 0.4rem;
    height: 0.4rem;
    position: relative;
    top: 0;
    right: 0.2rem;
`;

const DropdownTriggerContainer = styled.div<{ $isActive: boolean }>`
    display: flex;

    background: ${({ $isActive }: { $isActive: boolean }) =>
        $isActive ? "rgba(162, 180, 237, 0.38) !important" : "none"};

    :hover {
        background: rgba(175, 194, 255, 0.27);
    }
`;

interface ScheduleSelectorDropdownProps {
    user: User;
    activeName: string;
    primaryScheduleId: string;
    allSchedules: { [key: string]: ScheduleType };
    friendshipState: FriendshipState;
    displayOwnSchedule: (scheduleName: string) => void;
    readOnly: boolean;
    friendshipMutators: {
        fetchFriendSchedule: (friend: User) => void;
        fetchBackendFriendships: (user: User) => void;
        deleteFriendshipOnBackend: (user: User, friendPennkey: string) => void;
    };
    schedulesMutators: {
        copy: (scheduleName: string, sections: Section[]) => void;
        remove: (user: User, scheduleName: string, scheduleId: string) => void;
        rename: (oldName: string) => void;
        createSchedule: () => void;
        addFriend: () => void;
        showRequests: () => void;
        setPrimary: (user: User, scheduleName: string | null) => void;
    };
}

const ScheduleSelectorDropdown = ({
    user,
    activeName,
    primaryScheduleId,
    allSchedules,
    friendshipState,
    displayOwnSchedule,
    readOnly,
    friendshipMutators: {
        fetchFriendSchedule,
        deleteFriendshipOnBackend,
        fetchBackendFriendships,
    },
    schedulesMutators: {
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

    const hasFriends = friendshipState.acceptedFriends.length != 0;
    const numRequests = friendshipState.requestsReceived.length;

    // Used for box coloring, from StackOverflow:
    // https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
    const hashString = (s: string) => {
        let hash = 0;
        if (!s || s.length === 0) return hash;
        for (let i = 0; i < s.length; i += 1) {
            const chr = s.charCodeAt(i);
            hash = (hash << 5) - hash + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    };

    // step 2 in the CIS121 review: hashing with linear probing.
    // hash every section to a color, but if that color is taken, try the next color in the
    // colors array. Only start reusing colors when all the colors are used.
    const getColor = (() => {
        const colors = [
            Color.BLUE,
            Color.RED,
            Color.AQUA,
            Color.ORANGE,
            Color.GREEN,
            Color.PINK,
            Color.SEA,
            Color.INDIGO,
        ];
        // some CIS120: `used` is a *closure* storing the colors currently in the schedule
        let used: Color[] = [];
        return (c: string) => {
            if (used.length === colors.length) {
                // if we've used all the colors, it's acceptable to start reusing colors.
                used = [];
            }
            let i = Math.abs(hashString(c));
            while (used.indexOf(colors[i % colors.length]) !== -1) {
                i += 1;
            }
            const color = colors[i % colors.length];
            used.push(color);
            return color;
        };
    })();

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
        <ScheduleDropdownContainer ref={ref}>
            <ScheduleDropdownHeader>
                <DropdownTriggerContainer
                    $isActive={isActive}
                    onClick={() => {
                        fetchBackendFriendships(user);
                        setIsActive(!isActive);
                    }}
                    role="button"
                >
                    <span className="selected_name">
                        {readOnly && friendshipState.activeFriend
                            ? friendshipState.activeFriend.first_name +
                              "'s Schedule"
                            : activeName}
                    </span>
                    <DropdownTrigger>
                        <div aria-haspopup={true} aria-controls="dropdown-menu">
                            <Icon>
                                <i
                                    className={`fa fa-chevron-${
                                        isActive ? "up" : "down"
                                    }`}
                                    aria-hidden="true"
                                />
                            </Icon>
                        </div>
                    </DropdownTrigger>
                    {numRequests > 0 && <ReceivedRequestNotice />}
                </DropdownTriggerContainer>
                {!readOnly && (
                    <DownloadSchedulePromoContainer>
                        <DownloadScheduleInfo
                            href="https://support.google.com/calendar/answer/37118?sjid=16812697295393986554-NA&visit_id=638928653078159420-327839679&rd=1"
                            target="_blank"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <i
                                className="fa fa-info-circle fa-md"
                                aria-hidden="true"
                            />
                        </DownloadScheduleInfo>

                        <DownloadSchedulePromo
                            href={
                                allSchedules[activeName]
                                    ? `/api/plan/${allSchedules[activeName].id}/calendar/`
                                    : undefined
                            }
                            onClick={(e) => e.stopPropagation()}
                            download
                        >
                            <i
                                className="fa fa-download fa-sm"
                                aria-hidden="true"
                            />
                            Download Schedule
                        </DownloadSchedulePromo>
                    </DownloadSchedulePromoContainer>
                )}
            </ScheduleDropdownHeader>
            <DropdownMenu $isActive={isActive} role="menu">
                <DropdownContent>
                    {allSchedules &&
                        Object.entries(allSchedules)
                            .sort(([nameA, dataA], [nameB, dataB]) => {
                                /* Always putting primary schedule at the top, followed by the path registration schedule,
                                 * then rest of schedules should be ordered by created_at
                                 */

                                if (dataA.id === primaryScheduleId) return -1;
                                if (dataB.id === primaryScheduleId) return 1;
                                if (nameA == PATH_REGISTRATION_SCHEDULE_NAME)
                                    return -1;
                                if (nameB === PATH_REGISTRATION_SCHEDULE_NAME)
                                    return -1;

                                return dataA.created_at < dataB.created_at
                                    ? -1
                                    : 1;
                            })
                            .map(([name, data]) => {
                                const mutable =
                                    name !== PATH_REGISTRATION_SCHEDULE_NAME;
                                return (
                                    <DropdownButton
                                        allSchedules={allSchedules}
                                        key={data.id}
                                        isActive={
                                            name === activeName &&
                                            friendshipState.activeFriend ===
                                                null
                                        }
                                        makeActive={() => {
                                            setIsActive(false);
                                        }}
                                        isPrimary={
                                            primaryScheduleId === data.id
                                        }
                                        hasFriends={hasFriends}
                                        onClick={() => displayOwnSchedule(name)}
                                        text={name}
                                        mutators={{
                                            setPrimary: () => {
                                                if (
                                                    primaryScheduleId ===
                                                    data.id
                                                ) {
                                                    setPrimary(user, null);
                                                } else {
                                                    setPrimary(user, data.id);
                                                }
                                            },
                                            copy: () => {
                                                copy(
                                                    nextAvailable(
                                                        name,
                                                        allSchedules
                                                    ),
                                                    data.sections
                                                );
                                            },
                                            remove: mutable
                                                ? () =>
                                                      remove(
                                                          user,
                                                          name,
                                                          data.id
                                                      )
                                                : null,
                                            rename: mutable
                                                ? () => rename(name)
                                                : null,
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
                                    <div>
                                        Click{" "}
                                        <i
                                            className="fa fa-user"
                                            aria-hidden="true"
                                        />{" "}
                                        to set your shared schedule
                                    </div>
                                </div>
                            ) : (
                                "Add a friend to share a schedule"
                            )}
                        </div>
                        {friendshipState.acceptedFriends.map((friend, i) => (
                            <FriendButton
                                key={i}
                                friendName={`${friend.first_name} ${friend.last_name}`}
                                display={() => fetchFriendSchedule(friend)}
                                removeFriend={() => {
                                    deleteFriendshipOnBackend(
                                        user,
                                        friend.username
                                    );
                                }}
                                isActive={
                                    readOnly &&
                                    friendshipState.activeFriend &&
                                    friendshipState.activeFriend.username ===
                                        friend.username
                                }
                                color={getColor(friend.username)}
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
                            <PendingRequestsNum>
                                {numRequests}
                            </PendingRequestsNum>
                        </PendingRequests>
                    </FriendContent>
                </DropdownContent>
            </DropdownMenu>
        </ScheduleDropdownContainer>
    );
};

export default ScheduleSelectorDropdown;
