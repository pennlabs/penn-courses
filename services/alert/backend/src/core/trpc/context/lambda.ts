import type { CreateAWSLambdaContextOptions } from '@trpc/server/adapters/aws-lambda'
import type { APIGatewayProxyEvent, APIGatewayProxyEventV2 } from 'aws-lambda'

import createContext, { type Context } from '@/core/trpc/context/base'

const createLambdaContext = async ({
	event: { headers },
}: CreateAWSLambdaContextOptions<
	APIGatewayProxyEvent | APIGatewayProxyEventV2
>): Promise<Context> =>
	createContext({
		headers,
	})

export default createLambdaContext
