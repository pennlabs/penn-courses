import { PropsWithChildren } from 'react'
import {
	AuthProvider as OIDCAuthProvider,
	type AuthProviderProps,
} from 'react-oidc-context'

import { userManager } from '@/core/auth'

const config = {
	userManager,
	onSigninCallback: user => {
		console.log(user)
		window.history.replaceState({}, document.title, '/')
	},
} satisfies AuthProviderProps

export const AuthProvider: React.FC<PropsWithChildren> = ({ children }) => {
	return <OIDCAuthProvider {...config}>{children}</OIDCAuthProvider>
}
