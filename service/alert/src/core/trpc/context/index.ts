import { IncomingHttpHeaders } from "http2"

import db from "@/core/db"

export interface BaseContext {
	headers: IncomingHttpHeaders
	db: typeof db
}

export type Context = BaseContext

const createContext = async ({
	headers,
}: {
	headers: IncomingHttpHeaders
}): Promise<Context> => {
	const baseContext: Context = {
		headers,
		db,
	}
	return baseContext
}

export default createContext
