import type { CreateFastifyContextOptions } from '@trpc/server/adapters/fastify'

import createContext, { type Context } from '@/core/trpc/context/base'

const createFastifyContext = async ({
	req,
}: CreateFastifyContextOptions): Promise<Context> =>
	createContext({
		headers: req.headers,
	})

export default createFastifyContext
