import type { AppRouter } from '@pennlabs/pca-backend/router'
import { createTRPCReact } from '@trpc/react-query'
import type { inferRouterInputs, inferRouterOutputs } from '@trpc/server'

export const trpc = createTRPCReact<AppRouter>()

export type RouterInput = inferRouterInputs<AppRouter>
export type RouterOutput = inferRouterOutputs<AppRouter>
