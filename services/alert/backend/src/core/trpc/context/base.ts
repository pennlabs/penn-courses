import type { IncomingHttpHeaders } from 'http2'

export interface BaseContext {
	headers: IncomingHttpHeaders
}

export type Context = BaseContext

const createContext = async ({
	headers,
}: {
	headers: IncomingHttpHeaders
}): Promise<Context> => {
	const baseContext: Context = {
		headers,
	}
	return baseContext
}

export default createContext
