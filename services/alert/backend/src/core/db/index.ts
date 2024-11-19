export * from 'drizzle-orm'
import { drizzle as pgDrizzle } from 'drizzle-orm/node-postgres'
import pg from 'pg'

import * as schema from './schema'

import { ENV } from '@/core/env'

const db = (() => {
	const pool = new pg.Pool({
		connectionString: ENV.DATABASE_URL,
	})
	return pgDrizzle(pool, {
		schema,
		logger: true,
	})
})()

export default db
