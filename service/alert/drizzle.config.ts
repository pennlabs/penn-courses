import type { Config } from "drizzle-kit"
import { ENV } from "./src/core/env"

export default {
	dbCredentials: {
		connectionString: ENV.DATABASE_URI,
	},
	tablesFilter: ["alert_*"],
	schema: "./src/db/schema.ts",
	out: "./drizzle",
	driver: "pg",
} satisfies Config
