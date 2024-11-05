import { SendEmailCommand, SESv2Client } from "@aws-sdk/client-sesv2"

const client = new SESv2Client({})

export const sendCourseAlertEmail = async (args: {
	section_id: string
	recipient: string[]
}) => {
	const { section_id, recipient } = args
	const sendEmailCommand = new SendEmailCommand({
		FromEmailAddress: "noreply@penncoursealert.com",
		Destination: {
			BccAddresses: recipient,
		},
		Content: {
			Template: {
				TemplateName: "PennCourseAlert",
				TemplateData: JSON.stringify({
					courseCode: section_id,
				}),
			},
		},
	})
	await client.send(sendEmailCommand)
}
