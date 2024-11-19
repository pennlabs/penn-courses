import { awsLambdaRequestHandler } from '@trpc/server/adapters/aws-lambda'
import type {
	APIGatewayProxyEvent,
	APIGatewayProxyEventV2,
	Context as APIGWContext,
} from 'aws-lambda'

import createLambdaContext from '@/core/trpc/context/lambda'
import appRouter from '@/router'

const generateCORSHeaders = (origin: string) => ({
	'Access-Control-Allow-Origin': origin,
	'Access-Control-Allow-Headers': 'Origin, Content-Type, Authorization',
	'Access-Control-Allow-Methods':
		'DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT',
})

const trpcHandler = awsLambdaRequestHandler({
	router: appRouter,
	batching: {
		enabled: true,
	},
	createContext: createLambdaContext,
	onError: ({ error }) => {
		console.error(error)
	},
	responseMeta: ({ ctx }) => {
		if (!ctx?.headers?.origin) return {}
		return {
			headers: generateCORSHeaders(ctx.headers.origin),
		}
	},
})

interface HealthCheckEvent {
	health: 'check'
}

const isHealthCheckEvent = (event: unknown): event is HealthCheckEvent =>
	(event as { health: string })?.health === 'check'

const getHTTPMethod = (event: APIGatewayProxyEvent | APIGatewayProxyEventV2) =>
	Object.hasOwn(event.requestContext, 'httpMethod')
		? (event as APIGatewayProxyEvent).requestContext.httpMethod
		: (event as APIGatewayProxyEventV2).requestContext.http.method

export const handler = async (
	event: APIGatewayProxyEvent | APIGatewayProxyEventV2 | HealthCheckEvent,
	context: APIGWContext,
) => {
	if (isHealthCheckEvent(event)) {
		return {
			statusCode: 200,
			body: JSON.stringify({
				status: 'ok',
			}),
		}
	}

	const origin = event.headers?.origin
	const method = getHTTPMethod(event)

	if (method === 'OPTIONS' && origin) {
		return {
			statusCode: 200,
			headers: generateCORSHeaders(origin),
			body: JSON.stringify({
				status: 'ok',
			}),
		}
	}

	return trpcHandler(event, context)
}
