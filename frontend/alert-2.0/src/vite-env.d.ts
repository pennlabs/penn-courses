/// <reference types="vite/client" />

interface ImportMetaEnv {
	readonly VITE_BACKEND_BASE_URL: string
	readonly VITE_BASE_URL: string
	readonly VITE_CLIENT_ID: string
	// more env variables...
}

interface ImportMeta {
	readonly env: ImportMetaEnv
}
