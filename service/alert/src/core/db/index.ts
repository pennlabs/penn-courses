import postgres from "postgres"
import { drizzle } from "drizzle-orm/postgres-js"
import { ENV } from "@/core/env"

const queryClient = postgres(ENV.DATABASE_URI)
const db = drizzle(queryClient)

export default db
