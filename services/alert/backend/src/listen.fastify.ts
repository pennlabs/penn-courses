import 'dotenv/config'

import { fastifyCors, type FastifyCorsOptions } from '@fastify/cors'
import {
	fastifyTRPCPlugin,
	type FastifyTRPCPluginOptions,
} from '@trpc/server/adapters/fastify'
import fastify from 'fastify'

import createFastifyContext from '@/core/trpc/context/fastify'
import router, { type AppRouter } from '@/router'

const server = fastify()

/**
 * fastify register type is broken. Need to define Options explicitly.
 */
server.register<FastifyCorsOptions>(fastifyCors, {
	origin: (origin, callback) => {
		if (!origin) return callback(null, true)
		return callback(null, true)
	},
})

/**
 * fastify register type is broken. Need to define Options explicitly.
 */
server.register(fastifyTRPCPlugin, {
	prefix: '/trpc',
	trpcOptions: {
		batching: {
			enabled: true,
		},
		router,
		createContext: createFastifyContext,
		onError: ({ error }) => {
			console.error(error)
		},
	} satisfies FastifyTRPCPluginOptions<AppRouter>['trpcOptions'],
})

const PORT = Number(process.env.PORT ?? 8000)

const listen = async () => {
	try {
		const address = await server.listen({
			port: PORT,
			host: '0.0.0.0',
		})
		await server.ready()
		console.log(`🚀 Server Listening on: ${address}`)
	} catch (error) {
		console.error(error)
		process.exit(1)
	}
}

const main = async () => {
	try {
		await listen()
	} catch (error) {
		console.error(error)
		process.exit(1)
	}
}

main()
