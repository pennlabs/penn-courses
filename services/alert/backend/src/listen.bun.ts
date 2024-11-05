import { createBunServeHandler } from 'trpc-bun-adapter'

import { ENV } from '@/core/env'
import createBunContext from '@/core/trpc/context/bun'
import appRouter from '@/router'

const server = createBunServeHandler(
	/*
			trpc-bun-adapter uses tRPC's implementation of fetch handler,
			which requires the "req" type for incoming requests,
			but it is automatically handled by the adapter.
		*/
	{
		endpoint: '/trpc',
		router: appRouter,
		batching: {
			enabled: true,
		},
		createContext: createBunContext,
		responseMeta: () => {
			return {
				status: 200,
				headers: {
					'Access-Control-Allow-Origin': '*',
					'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
					'Access-Control-Allow-Headers': 'Content-Type, Authorization',
				},
			}
		},
	},
	{
		port: ENV.PORT ?? 8000,
		development: ENV.NODE_ENV === 'development',
		fetch: () =>
			new Response(null, {
				status: 404,
			}),
	},
)

export default server
