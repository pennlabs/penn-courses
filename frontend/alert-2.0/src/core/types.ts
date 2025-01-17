import { RouterOutput } from '@/core/trpc'

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
	LECTURE = 'LEC',
	LAB = 'LAB',
	MASTERS_THESIS = 'MST',
	RECITATION = 'REC',
	SEMINAR = 'SEM',
	SENIOR_THESIS = 'SRT',
	STUDIO = 'STU',
	UNDEFINED = '***',
}

export type CourseSection = RouterOutput['course']['searchSection'][number]
