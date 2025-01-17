import { defineConfig } from 'drizzle-kit'

import { ENV } from '@/core/env'

export default defineConfig({
	schema: './src/core/db/schema/index.ts',
	out: './drizzle',
	dialect: 'postgresql',
	dbCredentials: {
		url: ENV.DATABASE_URL,
	},
	introspect: {
		casing: 'camel',
	},
	verbose: true,
	tablesFilter: 'courses_course',
})
