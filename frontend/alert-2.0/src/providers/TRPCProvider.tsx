import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { httpBatchLink, loggerLink } from '@trpc/client'
import { PropsWithChildren } from 'react'
import superjson from 'superjson'

import { userManager } from '@/core/auth'
import { isTRPCClientError } from '@/core/error'
import { trpc } from '@/core/trpc'

const queryClient = new QueryClient({
	defaultOptions: {
		mutations: {},
		queries: {
			structuralSharing: false,
			throwOnError: true,
			retry: (count, error) => {
				if (isTRPCClientError(error)) {
					if (error.data?.code === 'UNAUTHORIZED' && count > 1) {
						return false
					}
				}
				return count < 4
			},
			retryDelay: (
				attemptIndex, // exponential backoff
			) => Math.min(500 * 2 ** attemptIndex, 30 * 1000),
		},
	},
})

const trpcClient = trpc.createClient({
	links: [
		loggerLink(),
		httpBatchLink({
			url: import.meta.env.VITE_BACKEND_BASE_URL,
			transformer: superjson,
			headers: async () => {
				try {
					const user = await userManager.getUser()
					const idToken = user?.id_token
					if (!idToken) throw new Error('No access token')
					return {
						Authorization: `Bearer ${idToken}`,
					}
				} catch (error) {
					return {}
				}
			},
		}),
	],
})

const TRPCProvider: React.FC<PropsWithChildren> = ({ children }) => {
	return (
		<trpc.Provider client={trpcClient} queryClient={queryClient}>
			<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
		</trpc.Provider>
	)
}

export default TRPCProvider
