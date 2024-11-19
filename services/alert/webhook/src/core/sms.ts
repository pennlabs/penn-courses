import { SNSClient, PublishCommand } from "@aws-sdk/client-sns"

const client = new SNSClient({region: "us-east-1"})

export const sendCourseAlertSMS = async (args: {
	section_id: string
	recipient: string[]
}) => {
	const { section_id, recipient } = args
    const commandPromises = recipient.map((phoneNumber) =>
        client.send(
            new PublishCommand({
                Message: `PennCourseAlert: ${section_id} is now open!`,
                PhoneNumber: phoneNumber,
            })
        )
    )
    const results = await Promise.allSettled(commandPromises)
    return results.filter((result, _) => result.status !== "fulfilled")
}
