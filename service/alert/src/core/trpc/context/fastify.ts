import { CreateFastifyContextOptions } from "@trpc/server/adapters/fastify"

import createContext, { Context } from "@/core/trpc/context"

const createFastifyContext = async ({
	req,
}: CreateFastifyContextOptions): Promise<Context> =>
	createContext({
		headers: req.headers,
	})

export default createFastifyContext
