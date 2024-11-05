import { sendCourseAlertEmail } from "@/core/ses"

sendCourseAlertEmail({
	recipient: ["esinx@seas.upenn.edu"],
	section_id: "CIS-120-001",
})
