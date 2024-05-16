import { initTRPC } from "@trpc/server"
import superjson from "superjson"

import type { Context } from "./context"

const t = initTRPC.context<Context>().create({
	transformer: superjson,
})

export const middleware = t.middleware
export const router = t.router
export const procedure = t.procedure
export const mergeRouters = t.mergeRouters
