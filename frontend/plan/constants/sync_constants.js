// The source of all constants related to schedule syncing

// The minimum interval at which calls can be made to the backend
export const MIN_FETCH_INTERVAL = 500;

// The interval at which to check whether the frontend and backend are up-to-date with one another
export const SYNC_INTERVAL = 5000;

// Whether to notify the user not to have multiple tabs open
export const DISABLE_MULTIPLE_TABS = false;

// The max number of deletion attempts (to send to the backend) before giving up
export const MAX_DELETION_ATTEMPTS = 2;

/* The minimum time difference in milliseconds between a schedule's local and remote timestamp
 required for the schedule's local version to be overridden before changes to it are pushed */
export const MIN_TIME_DIFFERENCE = 10000;

/* The maximum number of times to try creating a schedule before giving up */
export const MAX_CREATION_ATTEMPTS = 2;
