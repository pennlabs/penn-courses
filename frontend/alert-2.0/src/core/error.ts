import type { AppRouter } from '@pennlabs/pca-backend/router'
import { TRPCClientError } from '@trpc/client'

export const isTRPCClientError = (
	error: unknown,
): error is TRPCClientError<AppRouter> => {
	if (error instanceof Error) {
		return error.name === 'TRPCClientError'
	}
	return false
}
