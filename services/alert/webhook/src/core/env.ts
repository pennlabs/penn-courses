import "dotenv/config"

import { parseEnv } from "znv"
import { z } from "zod"

const schema = {
	DATABASE_URL: z.string().url(),
	CURRENT_SEMESTER: z.string(),
	PUSH_ENDPOINT: z.string(),
	PUSH_TOKEN: z.string(),
}

const $schema = z.object(schema)
type Schema = z.infer<typeof $schema>

export const ENV: Schema = parseEnv(process.env, schema)
