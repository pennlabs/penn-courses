import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export const PCAHeader: React.FC = () => {
	return (
		<div
			className={cn(
				'flex',
				'flex-col',
				'items-center',
				'justify-center',
				'space-y-2',
			)}
		>
			<div
				className={cn('flex', 'items-center', 'justify-center', 'space-x-4')}
			>
				<img
					src="/assets/icons/PCA_logo.svg"
					className={cn('w-12', 'h-12', 'select-none', 'pointer-events-none')}
				/>
				<div
					className={cn(
						'text-3xl',
						'font-bold',
						'select-none',
						'pointer-events-none',
					)}
				>
					Penn Course Alert
				</div>
				<Badge>2.0</Badge>
			</div>
			<div className={cn('text-sm', 'text-gray-500', 'text-center')}>
				Get alerted when a course opens up
			</div>
		</div>
	)
}
