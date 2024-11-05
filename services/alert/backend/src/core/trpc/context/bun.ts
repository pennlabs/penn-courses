import type { CreateBunContextOptions } from 'trpc-bun-adapter'

import createContext, { type Context } from '@/core/trpc/context/base'

const createBunContext = async ({
	req,
}: CreateBunContextOptions): Promise<Context> =>
	createContext({
		headers: req.headers.toJSON(),
	})

export default createBunContext
