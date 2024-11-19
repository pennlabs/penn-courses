import { createRouter, RouterProvider } from '@tanstack/react-router'
import { Log } from 'oidc-client-ts'
import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'

import './index.css'

import { routeTree } from './routeTree.gen'

import { AuthProvider } from '@/providers/AuthProvider'
import TRPCProvider from '@/providers/TRPCProvider'

Log.setLogger(console)

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
	interface Register {
		router: typeof router
	}
}

// Render the app
const rootElement = document.getElementById('root') as HTMLElement
if (!rootElement.innerHTML) {
	const root = ReactDOM.createRoot(rootElement)
	root.render(
		<StrictMode>
			<AuthProvider>
				<TRPCProvider>
					<RouterProvider router={router} />
				</TRPCProvider>
			</AuthProvider>
		</StrictMode>,
	)
}
