import { TRPCError } from "@trpc/server"
import jwt, { JwtPayload } from "jose"

import { ENV } from "@/core/env"
import { middleware, procedure } from "@/core/trpc"

export interface LabsUserProcedurePayload extends JwtPayload {
	aud: string
	exp: number
	sub: string
	email?: string
	phone: string
	role: string
	aal: string
	amr: {
		method: string
		timestamp: number
	}[]
	session_id: string
}

/**
 * @description gotrue-authorized procedure
 */
const labsUserProcedure = procedure.use(
	middleware(async ({ ctx, next }) => {
		const { authorization, Authorization } = ctx.headers
		const token = (
			authorization ??
			(Array.isArray(Authorization) ? Authorization?.[0] : Authorization)
		)?.match(/Bearer (.+)/)?.[1]

		if (!token) {
			throw new TRPCError({
				code: "UNAUTHORIZED",
				message: "Unauthorized",
			})
		}
		const payload = jwt.verify(
			token,
			ENV.AUTH_SECRET
		) as LabsUserProcedurePayload
		return next({
			ctx: {
				...ctx,
				// convenience alias for other procedures
				user: {
					id: payload.sub,
					phone: payload.phone,
				},
				payload,
			},
		})
	})
)

export default labsUserProcedure
