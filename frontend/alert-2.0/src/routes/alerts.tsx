import { createFileRoute } from '@tanstack/react-router'
import { Suspense } from 'react'
import { toast } from 'sonner'

import { StatusIndicator } from '@/components/StatusIndicator'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { trpc } from '@/core/trpc'
import { Status } from '@/core/types'
import { cn } from '@/lib/utils'

const Content: React.FC = () => {
	const [alerts, { refetch: refetchAlerts }] =
		trpc.alert.list.useSuspenseQuery()
	const { mutateAsync: unregister } = trpc.alert.unregister.useMutation()

	const activeAlerts = alerts.filter(alert => alert.deletedAt === null)
	const inactiveAlerts = alerts.filter(alert => alert.deletedAt !== null)

	return (
		<div className={cn('mt-4')}>
			<h2 className={cn('text-lg', 'font-bold', 'text-slate-700')}>
				Active Alerts
			</h2>
			<div
				className={cn('mt-2', 'grid', 'gap-2')}
				style={{
					gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
				}}
			>
				{activeAlerts.length === 0 && (
					<div>
						<p>You have no alerts registered.</p>
					</div>
				)}
				{activeAlerts.map(alert => (
					<Card key={alert.id}>
						<CardContent className={cn('py-2', 'text-sm')}>
							<div
								className={cn(
									'flex',
									'items-center',
									'space-x-4',
									'justify-between',
								)}
							>
								<div className={cn('flex', 'items-center', 'space-x-4')}>
									<StatusIndicator status={alert.section.status as Status} />
									<div>
										<div className={cn('text-slate-600')}>
											{alert.course.title}
										</div>
										<div className={cn('font-bold')}>{alert.section.code}</div>
										<div className={cn('text-slate-600', 'font-bold')}>
											{alert.course.semester}
										</div>
									</div>
								</div>
								<div
									role="button"
									className={cn('cursor-pointer')}
									onClick={async () => {
										try {
											await unregister({ registrationIds: [alert.id] })
											toast.success(
												`Unregistered alert for ${alert.section.code}`,
											)
											refetchAlerts()
										} catch (error) {
											toast.error('Failed to unregister alert')
										}
									}}
								>
									<img
										src="/assets/icons/trash.svg"
										alt="Delete"
										className={cn('w-4', 'h-4')}
									/>
								</div>
							</div>
						</CardContent>
					</Card>
				))}
			</div>
			<h2 className={cn('text-lg', 'font-bold', 'text-slate-700', 'mt-4')}>
				Inactive Alerts
			</h2>
			<div
				className={cn('mt-2', 'grid', 'gap-2')}
				style={{
					gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
				}}
			>
				{inactiveAlerts.length === 0 && (
					<div>
						<p>You have no inactive alerts.</p>
					</div>
				)}
				{inactiveAlerts.map(alert => (
					<Card
						key={alert.id}
						className={cn('opacity-50', 'pointer-events-none')}
					>
						<CardContent className={cn('py-2', 'text-sm')}>
							<div
								className={cn(
									'flex',
									'items-center',
									'space-x-4',
									'justify-between',
								)}
							>
								<div className={cn('flex', 'items-center', 'space-x-4')}>
									<StatusIndicator status={alert.section.status as Status} />
									<div>
										<div className={cn('text-slate-600')}>
											{alert.course.title}
										</div>
										<div className={cn('font-bold')}>{alert.section.code}</div>
										<div className={cn('text-slate-600', 'font-bold')}>
											{alert.course.semester}
										</div>
									</div>
								</div>
							</div>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	)
}

const Alerts: React.FC = () => {
	return (
		<main className={cn('max-w-[960px]', 'm-auto')}>
			<h1 className={cn('text-xl', 'font-bold')}>Your Alerts</h1>
			<Suspense
				fallback={
					<div
						className={cn('mt-4', 'grid', 'gap-2')}
						style={{
							gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
						}}
					>
						{new Array(9).fill(null).map((_, i) => (
							<Skeleton className={cn('h-12')} key={i} />
						))}
					</div>
				}
			>
				<Content />
			</Suspense>
		</main>
	)
}

export const Route = createFileRoute('/alerts')({
	component: Alerts,
})
