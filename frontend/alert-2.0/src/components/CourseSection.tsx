import { match } from 'ts-pattern'

import { StatusIndicator } from '@/components/StatusIndicator'
import { Badge } from '@/components/ui/badge'
import { Activity, type CourseSection } from '@/core/types'
import { cn } from '@/lib/utils'

interface Props {
	section: CourseSection
	className?: string
}

const classOfActivity = (activity: Activity) =>
	match(activity)
		.with(Activity.LECTURE, () =>
			cn('bg-blue-100', 'hover:bg-blue-100', 'text-blue-600'),
		)
		.with(Activity.RECITATION, () =>
			cn('bg-yellow-100', 'hover:bg-yellow-100', 'text-yellow-600'),
		)
		.with(Activity.LAB, () =>
			cn('bg-green-100', 'hover:bg-green-100', 'text-green-600'),
		)
		.otherwise(() => cn('bg-gray-100', 'hover:bg-gray-100', 'text-gray-600'))

export const CourseSectionContent: React.FC<Props> = ({
	section,
	className,
}) => {
	return (
		<div
			className={cn(
				'flex',
				'justify-between',
				'items-center',
				'text-sm',
				className,
			)}
		>
			<div className={cn('flex', 'items-center', 'space-x-4')}>
				<StatusIndicator status={section.status} />
				<div>
					<div className={cn('text-slate-600')}>{section.course_title}</div>
					<div className={cn('font-bold')}>{section.section_id}</div>
					<div className={cn('text-slate-600')}>
						{section.instructors.length > 0
							? section.instructors.map(inst => inst.name).join(', ')
							: 'N/A'}
					</div>
				</div>
			</div>
			<div className={cn('flex', 'flex-col', 'space-y-2', 'items-end')}>
				<Badge
					className={cn(
						classOfActivity(section.activity),
						'shadow-none',
						'hover:none',
					)}
				>
					{section.activity}
				</Badge>
			</div>
		</div>
	)
}
