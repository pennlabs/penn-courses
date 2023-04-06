import { doAPIRequest } from ".";
import getCsrf from "../components/csrf";

/**
 * Pulls user's friends from the backend
 */
export const fetchFriendships = (callback, user) => {
    doAPIRequest("/base/friendship")
        .then((res) => {
            return res.json();
        })
        .then((friendships) => {
            const requestsReceived = friendships.filter(
                (fs) => fs.status == "S" && fs.sender.username != user.username
            );

            const requestsSent = friendships.filter(
                (fs) => fs.status == "S" && fs.sender.username == user.username
            );

            const friends = friendships
                .filter((fs) => fs.status == "A")
                .map((fs) =>
                    fs.recipient.username === user.username
                        ? fs.sender
                        : fs.recipient
                );

            callback({
                received: requestsReceived,
                sent: requestsSent,
                friends,
            });
        })
        .catch((error) => console.log(error));
};

export const sendFriendRequest = async (pennkey) => {
    const pennKeyObj = {
        pennkey,
    };

    const init = {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(pennKeyObj),
    };
    const res = await doAPIRequest("/base/friendship/", init);
    if (res.status == 200) {
        // request accepted
        // blob friendship created successfully?
        return {
            message: "",
            error: false,
        };
    }
    if (res.status == 201) {
        // friendship not requested before
        // request created
        // blob friendship request sent
        // friendship requested before
        // request created
        // blob friendship request sent
        return {
            message: "",
            error: false,
        };
    }
    if (res.status == 404) {
        // pennkey not found
        // blob pennkey not found
        return {
            message: "User not found.",
            error: true,
        };
    }
    if (res.status == 409) {
        // request pending
        // blob friendship request pending
        return {
            message: "Friendship request still pending.",
            error: true,
        };
    }
    return { message: "", error: false };
};

export const rejectFriendRequest = async (pennkey) => {
    const pennIdObj = {
        pennkey,
    };

    const init = {
        method: "DELETE",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(pennIdObj),
    };
    try {
        return await doAPIRequest("/base/friendship/", init);
    } catch (error) {
        return console.log(error);
    }
};

export const fetchFriendPrimarySchedule = (pennkey, isDisplaying, callback) => {
    doAPIRequest("/plan/primary-schedules/")
        .then((res) => res.json())
        .then((schedules) => {
            return schedules.find((sched) => sched.user.username === pennkey);
        })
        .then((foundSched) => {
            if (foundSched) {
                isDisplaying(foundSched.user.first_name + "'s Schedule");
                callback(foundSched.schedule.sections);
            } else {
                isDisplaying("Not Found");
                callback({ sections: [] });
            }
        })
        .catch((error) => {
            error;
        });
};