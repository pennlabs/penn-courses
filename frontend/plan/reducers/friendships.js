import {
    UPDATE_FRIENDSHIPS_ON_FRONTEND,
    SWITCH_ACTIVE_FRIEND,
} from "../actions/friendshipUtil";
import { Color } from "../types";

const initialState = {
    pulledFromBackend: false,
    activeFriend: null,
    activeFriendSchedule: null,
    acceptedFriends: [],
    requestsReceived: [],
    requestsSent: [],
};

const handleUpdateFriendsOnFrontend = (state, action) => {
    let newState = { ...state };
    newState = {
        ...newState,
        acceptedFriends: action.friends,
        requestsReceived: action.received,
        requestsSent: action.sent,
        pulledFromBackend: true,
    };

    return newState;
};

// Used for box coloring, from StackOverflow:
// https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
const hashString = (s) => {
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
    let used = [];
    return (c) => {
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

export const friendships = (state = initialState, action) => {
    switch (action.type) {
        case SWITCH_ACTIVE_FRIEND:
            return {
                ...state,
                activeFriend: action.friend,
                activeFriendSchedule: action.schedule
                    ? {
                          found: action.found,
                          sections: action.schedule.sections.map((section) => ({
                              ...section,
                              color: getColor(section.id),
                          })),
                          id: action.schedule.id,
                          pushedToBackend: true,
                          updated_at: Date.now(),
                          created_at: new Date(
                              action.schedule.created_at
                          ).getTime(),
                      }
                    : null,
            };
        case UPDATE_FRIENDSHIPS_ON_FRONTEND:
            return handleUpdateFriendsOnFrontend(state, action);
        default:
            return {
                ...state,
            };
    }
};
