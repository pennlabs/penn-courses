import { keepPreviousData } from '@tanstack/react-query'
import { useState } from 'react'
import { useDebounce } from 'use-debounce'

import { AutoComplete, ItemEntry } from '@/components/autocomplete'
import { CourseSectionContent } from '@/components/CourseSection'
import { trpc } from '@/core/trpc'
import { CourseSection } from '@/core/types'
import { cn } from '@/lib/utils'

interface Props {
	onCourseSectionSelected?: (courseSection: CourseSection) => void
}

const ItemComponent: React.FC<{ item: ItemEntry<CourseSection> }> = ({
	item: { value },
}) => {
	return (
		<CourseSectionContent
			section={value}
			className={cn('w-full', 'hover:cursor-pointer')}
		/>
	)
}

export const CourseSectionAutocomplete: React.FC<Props> = ({
	onCourseSectionSelected,
}) => {
	const [query, setQuery] = useState('')
	const [debouncedQuery] = useDebounce(query, 500)
	const {
		data: sections,
		isLoading,
		isPlaceholderData,
	} = trpc.course.searchSection.useQuery(
		{
			query: debouncedQuery,
			limit: 20,
		},
		{
			placeholderData: keepPreviousData,
			enabled: () => debouncedQuery.length > 0,
		},
	)
	return (
		<div>
			<AutoComplete
				items={
					sections?.map(section => ({
						id: section.section_id,
						value: section,
					})) ?? []
				}
				ItemComponent={ItemComponent}
				searchValue={query}
				onSearchValueChange={setQuery}
				placeholder="CIS-1200"
				onSelect={({ value }) => onCourseSectionSelected?.(value)}
				isLoading={isLoading}
				emptyMessage={
					debouncedQuery.length > 0 && !isPlaceholderData
						? 'No courses found'
						: 'Start typing to search!'
				}
			/>
		</div>
	)
}
