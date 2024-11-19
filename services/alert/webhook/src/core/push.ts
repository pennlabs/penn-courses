import { fetch } from "cross-fetch"
import { ENV } from "./env";

export const sendCourseAlertPush = async (args: {
	section_id: string
	recipient: string[]
}) => {
	const { section_id, recipient } = args

    const res = await fetch(ENV.PUSH_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${ENV.PUSH_TOKEN}`
        },
        body: JSON.stringify({
            usernames: recipient,
            service: "COURSES",
            title: `${section_id} is now open!`,
            body: `${section_id} just opened up!`
        })
    })
    return res.json()
}
