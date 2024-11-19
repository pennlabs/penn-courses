import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import React from 'react'
import { ErrorBoundary, FallbackProps } from 'react-error-boundary'
import { useAuth } from 'react-oidc-context'
import { useDebounce } from 'use-debounce'

import { PCAHeader } from '@/components/PCAHeader'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
	NavigationMenu,
	NavigationMenuItem,
	NavigationMenuLink,
	NavigationMenuList,
	navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu'
import { Toaster } from '@/components/ui/sonner'
import { userManager } from '@/core/auth'
import { isTRPCClientError } from '@/core/error'
import { cn } from '@/lib/utils'

const PingLoadingIndicator: React.FC = () => (
	<div className={cn('bg-blue-500', 'w-4', 'h-4', 'relative', 'rounded-full')}>
		<div
			className={cn(
				'bg-blue-500',
				'absolute',
				'rounded-full',
				'w-4',
				'h-4',
				'animate-ping',
			)}
		/>
	</div>
)

const Navbar: React.FC = () => {
	const auth = useAuth()
	const profile = auth.user?.profile
	const initials = profile?.name
		?.split(' ')
		.map(n => n[0])
		.join('')
		.toLocaleUpperCase()
		.slice(0, 2)
	return (
		<NavigationMenu
			className={cn(
				'max-w-[100vw]',
				'py-4',
				'px-8',
				'bg-white',
				'border-b-border',
				'border-b-2',
				'justify-between',
			)}
		>
			{/* width of avatar is fixed to w-10, we use this dummy to algin menu to center */}
			<div className={cn('w-10')} />
			<NavigationMenuList>
				<NavigationMenuItem>
					<NavigationMenuLink className={navigationMenuTriggerStyle()} asChild>
						<Link to="/">Home</Link>
					</NavigationMenuLink>
				</NavigationMenuItem>
				<NavigationMenuItem>
					<NavigationMenuLink className={navigationMenuTriggerStyle()} asChild>
						<Link to="/alerts">Alerts</Link>
					</NavigationMenuLink>
				</NavigationMenuItem>
			</NavigationMenuList>
			<Avatar>
				<AvatarFallback>{initials}</AvatarFallback>
			</Avatar>
		</NavigationMenu>
	)
}

const ErrorFallback: React.FC<FallbackProps> = ({
	error,
	resetErrorBoundary,
}) => {
	if (isTRPCClientError(error) && error.data?.code === 'UNAUTHORIZED') {
		try {
			userManager.signinSilent()
		} catch (error) {
			userManager.signinRedirect()
		}
	}
	return (
		<div>
			<p>Something went wrong:</p>
			<pre>{error.message}</pre>
			<Button onClick={resetErrorBoundary}>Try again</Button>
		</div>
	)
}

const Root: React.FC = () => {
	const auth = useAuth()
	const [debouncedAuthenticated] = useDebounce(auth.isAuthenticated, 300)
	return (
		<ErrorBoundary FallbackComponent={ErrorFallback}>
			<div className={cn('bg-slate-100', 'min-h-[100vh]')}>
				{!debouncedAuthenticated && (
					<div
						className={cn(
							'w-[100vw]',
							'h-[100vh]',
							'flex',
							'items-center',
							'justify-center',
						)}
					>
						<div
							className={cn('flex', 'flex-col', 'items-center', 'space-y-4')}
						>
							<PCAHeader />
							{auth.isLoading || auth.isAuthenticated ? (
								<PingLoadingIndicator />
							) : (
								<Button
									onClick={async () => {
										try {
											await auth.signinRedirect()
										} catch (error) {
											console.error(error)
										}
									}}
								>
									Login
								</Button>
							)}
						</div>
					</div>
				)}
				{debouncedAuthenticated && (
					<>
						<Navbar />
						<div className={cn('p-4')}>
							<Outlet />
						</div>
					</>
				)}
				<Toaster position="bottom-center" />
				{import.meta.env.DEV && <TanStackRouterDevtools />}
			</div>
		</ErrorBoundary>
	)
}

export const Route = createRootRoute({
	component: Root,
})
