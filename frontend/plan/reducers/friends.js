import {
  CLEAR_ALL_SCHEDULE_DATA,
  UPDATE_SCHEDULES,
  MARK_CART_SYNCED,
  MARK_SCHEDULE_SYNCED,
} from "../actions";
import {
  MIN_TIME_DIFFERENCE,
} from "../constants/sync_constants";

const DEFAULT_SCHEDULE_NAME = "Schedule";

// returns the default empty schedule
const generateEmptySchedule = (isDefault = true) => ({
  meetings: [],
  colorPalette: [],
  LocAdded: false,
  pushedToBackend: isDefault,
  backendCreationState: {
      creationQueued: false,
      creationAttempts: 0,
  },
  updated_at: 1,
});

// the state contains the following two pieces of data:
//  1. An object associating each schedule name with the schedule objecct
//  2. The name of the currently selected schedule
const initialState = {
  friends: { [DEFAULT_SCHEDULE_NAME]: generateEmptySchedule() },
  friendSelected: DEFAULT_SCHEDULE_NAME,
  friendsUpdated: 1,
};

/**
* Resets the cart to be empty, and assumes that it has not been pushed
* @param state The old state
* @return {{cartSections: [], cartPushedToBackend: boolean, cartUpdated: boolean}} New state
*/
const resetCart = (state) =>
  resetCartId({
      ...state,
      cartSections: [],
      cartPushedToBackend: true,
      cartUpdated: false,
  });

/**
* Takes in schedules from the backend; incorporates them into state; and returns the new state
* @param state The redux state
* @param schedulesFromBackend The schedules object sent by the backend
* @returns {{cartSections: *, cartPushedToBackend: boolean, schedules: *}}
*/
const processFriendUpdate = (state, friendsFromBackend) => {
  const newFriendObject = { ...(state.friends || {}) };
  const newState = { ...state };
  if (friendsFromBackend) {
      for (const {
          id: scheduleId,
          name,
          sections,
          semester,
          ...rest
      } of schedulesFromBackend) {
          const cloudUpdated = new Date(rest.updated_at).getTime();
          if (name === "cart") {
              const { cartUpdated } = state;
              const cartPushed = state.cartPushedToBackend;
              // If changes to the cart are still syncing, ignore the requested update
              if (
                  !cartPushed &&
                  cloudUpdated - cartUpdated < MIN_TIME_DIFFERENCE
              ) {
                  return state;
              }
              newState.cartId = scheduleId;
              if (!cartUpdated || cloudUpdated > cartUpdated) {
                  newCart = sections;
              }
          } else if (state.schedules[name]) {
              const selectedSched = state.schedules[name];
              const updated = selectedSched.updated_at;
              // If changes to the schedule are still syncing, ignore the requested update
              const pushed = selectedSched.pushedToBackend;
              if (
                  !pushed &&
                  updated &&
                  updated - cloudUpdated < MIN_TIME_DIFFERENCE
              ) {
                  return state;
              }
              newScheduleObject[name].id = scheduleId;
              newScheduleObject[name].backendCreationState = false;
              if (!updated || cloudUpdated > updated) {
                  newScheduleObject[name].meetings = sections;
              }
          } else if (!state.deletedSchedules[scheduleId]) {
              newScheduleObject[name] = {
                  meetings: sections,
                  semester,
                  id: scheduleId,
                  pushedToBackend: true,
                  updated_at: cloudUpdated,
              };
          }
      }
  }
  return {
      ...newState,
      schedules: newScheduleObject,
      cartSections: newCart,
      cartPushedToBackend: true,
  };
};

export const friends = (state = initialState, action) => {
  switch (action.type) {
      case CLEAR_ALL_SCHEDULE_DATA:
          return { ...initialState };
      case MARK_SCHEDULE_SYNCED:
          return {
              ...state,
              schedules: {
                  ...state.schedules,
                  [action.scheduleName]: {
                      ...state.schedules[action.scheduleName],
                      pushedToBackend: true,
                      backendCreationState: false,
                  },
              },
          };
      case MARK_CART_SYNCED:
          return {
              ...state,
              cartPushedToBackend: true,
          };
      case UPDATE_FRIENDS:
          return processFriendUpdate(state, action.friendsFromBackend);
      case CREATE_FRIENDSHIP:
        return {
            ...state,
            schedules: {
                ...state.schedules,
                [action.scheduleName]: generateEmptySchedule(false),
            },
            scheduleSelected: action.scheduleName,
        };
  }
};
