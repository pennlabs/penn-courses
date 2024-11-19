import type { APIGatewayProxyHandlerV2 } from "aws-lambda"
import { z, ZodError } from "zod"
import { Status } from "@/types/alert"
import { sendCourseAlertEmail } from "@/core/ses"
import { getRegisteredUsers } from "@/core/query"

const statusSchema = z.nativeEnum(Status)

const webhookPayloadSchema = z.object({
	previous_status: statusSchema,
	section_id: z.string(),
	section_id_normalized: z.string(),
	status: statusSchema,
	term: z.string(),
})

class BodyMissingError extends Error {
	constructor() {
		super("Request body is missing")
		this.name = "BodyMissingError"
	}
}

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
	try {
		if (!event.body) throw new BodyMissingError()
		const payload = webhookPayloadSchema.parse(JSON.parse(event.body))
		console.log("[org.pennlabs.courses.alert.webhook]: Incoming alert", payload)
		if (
			payload.previous_status !== Status.OPEN &&
			payload.status == Status.OPEN
		) {
			const users = await getRegisteredUsers(payload.section_id_normalized)
			console.log(
				`[org.pennlabs.courses.alert.webhook]: Targeting alert email to ${users.length} users`
			)
			await sendCourseAlertEmail({
				recipient: users.map((user) => user.email),
				section_id: payload.section_id,
			})
			console.log(
				`[org.pennlabs.courses.alert.webhook]: Sent alert email to ${users.length} users`
			)
		} else {
			console.log("[org.pennlabs.courses.alert.webhook]: Ignored alert")
		}
		return {
			statusCode: 200,
			body: JSON.stringify({
				message: "OK",
			}),
		}
	} catch (error) {
		console.error(error)
		if (
			error instanceof BodyMissingError ||
			error instanceof ZodError ||
			(error instanceof Error && error.name === "ValidationError")
		) {
			return {
				statusCode: 400,
				body: JSON.stringify({
					message: "Bad Request",
				}),
			}
		}
		return {
			statusCode: 500,
			body: JSON.stringify({
				message: "Unexpected Error",
			}),
		}
	}
}
