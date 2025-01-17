import { match } from 'ts-pattern'

import { Status } from '@/core/types'
import { cn } from '@/lib/utils'

const classOfStatus = (status: Status) =>
	match(status)
		.with(Status.OPEN, () => cn('bg-green-400'))
		.with(Status.CLOSED, () => cn('bg-red-400'))
		.otherwise(() => cn('bg-yellow-400'))

export const StatusIndicator: React.FC<{ status: Status }> = ({ status }) => {
	return (
		<div
			className={cn(
				classOfStatus(status),
				'w-2',
				'h-2',
				'relative',
				'rounded-full',
			)}
		>
			<div
				className={cn(
					classOfStatus(status),
					'absolute',
					'rounded-full',
					'w-2',
					'h-2',
					'animate-ping',
				)}
			/>
		</div>
	)
}
