import { CreateAWSLambdaContextOptions } from "@trpc/server/adapters/aws-lambda"
import { APIGatewayProxyEvent, APIGatewayProxyEventV2 } from "aws-lambda"

import createContext, { Context } from "@/core/trpc/context"

const createLambdaContext = async ({
	event: { headers },
}: CreateAWSLambdaContextOptions<
	APIGatewayProxyEvent | APIGatewayProxyEventV2
>): Promise<Context> =>
	createContext({
		headers,
	})

export default createLambdaContext
