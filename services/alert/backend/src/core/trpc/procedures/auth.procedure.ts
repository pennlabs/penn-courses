import { TRPCError } from '@trpc/server'
import * as jose from 'jose'

import { middleware, procedure } from '@/core/trpc'
import { LABS_PLATFORM_JWK } from '@/core/trpc/procedures/jwk'

interface RawPayload {
	sub: string
	name: string
	email: string
	pennkey: string
	pennid: number
	is_staff: boolean
	is_active: boolean
}

/**
 * @description Authorized procedure
 */
const authProcedure = procedure.use(
	middleware(async ({ ctx, next }) => {
		const { authorization, Authorization } = ctx.headers
		const token = (
			authorization ??
			(Array.isArray(Authorization) ? Authorization?.[0] : Authorization)
		)?.match(/Bearer (.+)/)?.[1]
		if (!token) {
			throw new TRPCError({
				code: 'UNAUTHORIZED',
				message: 'Unauthorized',
			})
		}
		const jwk = await jose.importJWK(LABS_PLATFORM_JWK)
		try {
			const { payload } = await jose.jwtVerify<RawPayload>(token, jwk, {
				clockTolerance: '1m',
			})
			return next({
				ctx: {
					...ctx,
					// convenience alias for other procedures
					user: {
						id: payload.sub,
						name: payload.name,
						email: payload.email,
						pennkey: payload.pennkey,
						pennid: payload.pennid,
						isStaff: payload.is_staff,
						isActive: payload.is_active,
					},
					payload,
				},
			})
		} catch (error) {
			throw new TRPCError({
				code: 'UNAUTHORIZED',
				message: 'Unauthorized',
			})
		}
	}),
)

export default authProcedure
