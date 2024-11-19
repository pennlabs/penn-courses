import { UserManager, WebStorageStateStore } from 'oidc-client-ts'

export const userManager = new UserManager({
	authority: 'https://platform.pennlabs.org/',
	client_id: import.meta.env.VITE_CLIENT_ID,
	redirect_uri: `${import.meta.env.VITE_BASE_URL}/callback`,
	scope: 'openid read',
	metadataUrl:
		'https://platform.pennlabs.org/accounts/.well-known/openid-configuration/',
	metadata: {
		authorization_endpoint: 'https://platform.pennlabs.org/accounts/authorize/',
		token_endpoint: 'https://platform.pennlabs.org/accounts/token/',
		jwks_uri: 'https://platform.pennlabs.org/accounts/.well-known/jwks.json',
	},
	automaticSilentRenew: true,
	includeIdTokenInSilentRenew: true,
	userStore: new WebStorageStateStore({ store: window.localStorage }),
})

console.log(userManager)
