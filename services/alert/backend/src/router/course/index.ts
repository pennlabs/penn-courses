import fetch from 'cross-fetch'
import { z } from 'zod'

import { procedure, router } from '@/core/trpc'

export enum Status {
	OPEN = 'O',
	CLOSED = 'C',
	CANCELLED = 'X',
	UNLISTED = '',
}

export enum Activity {
	CLINIC = 'CLN',
	DISSERTATION = 'DIS',
	INDEPENDENT_STUDY = 'IND',
	LAB = 'LAB',
	MASTERS_THESIS = 'MST',
	RECITATION = 'REC',
	SEMINAR = 'SEM',
	SENIOR_THESIS = 'SRT',
	STUDIO = 'STU',
	UNDEFINED = '***',
}

export interface CourseSection {
	section_id: string
	status: Status
	activity: Activity
	meeting_times: string
	instructors: {
		id: number
		name: string
	}[]
	course_code: string
	course_title: string
	semester: string
	registration_volume: number
}

type PennCoursesResponse = CourseSection[]

export const courseRouter = router({
	searchSection: procedure
		.input(
			z.object({
				query: z.string(),
				limit: z.number().optional(),
			}),
		)
		.query(async ({ input: { query, limit } }) => {
			if (query.length === 0) {
				return []
			}
			// TODO: implement native search
			const params = new URLSearchParams({
				search: query,
				format: 'json',
			})
			const res = await fetch(
				`https://penncourses.org/api/base/current/search/sections/?${params.toString()}`,
			)
			if (!res.ok) {
				throw new Error('Failed to fetch data')
			}
			const data: PennCoursesResponse = await res.json()
			return typeof limit === 'number' ? data.slice(0, limit) : data
		}),
})
