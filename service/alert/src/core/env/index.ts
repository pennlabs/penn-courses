import "dotenv/config"
import { parseEnv } from "znv"
import { z } from "zod"

export const ENV = parseEnv(process.env, {
	DATABASE_URI: z.string().url({
		message: "DATABASE_URI must be a valid URL",
	}),
})
