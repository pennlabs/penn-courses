import { useEffect, useState } from "react"
import { Course } from "../types/course"
import { Department } from "../types/department"
import { Instructor } from "../types/instructor"
import { API_DOMAIN, PCS_API_DOMAIN } from "../utils/api"
import { useDebouncedValue } from "./debounced-value"

enum FetchStatus {
	IDLE,
	LOADING,
	SUCCESS,
	ERROR,
}

export type CourseSearchResult = {
	Courses: Course[]
	Departments: Department[]
	Instructors: Instructor[]
}
export type CourseSearchOptions = {
	workLow: number
	workHigh: number
	difficultyLow: number
	difficultyHigh: number
	qualityLow: number
	qualityHigh: number
}

const normalizeQuery = (query: string): string => {
	query = query.replaceAll("-", " ")
	query = query.replaceAll(/[–—…«»‘’]/g, " ")
	query = query.replaceAll(/[“”]/g, '"')
	if (query.length >= 2 && query.slice(-2).match(/\w{2}/)) {
		const i = /\w+$/.exec(query)!.index
		const partial = query.substring(i)
		query = query.substring(0, i) + `(${partial}|${partial}*|%${partial}%)`
	} else if (query.length == 1) {
		query = `(${query}|${query}*)`
	} else if (query.length >= 1 && query.slice(-1).match(/\w/)) {
		query = query.slice(0, -1)
	}
	return query
}

const fetchQuery = async (
	query: string,
	options: CourseSearchOptions = {
		workLow: 0,
		workHigh: 4,
		difficultyLow: 0,
		difficultyHigh: 4,
		qualityLow: 0,
		qualityHigh: 4,
	}
) => {
	const normalizedQuery = normalizeQuery(query)
	const urlParams = new URLSearchParams(
		Object.entries(options).map(([k, v]) => [k, v.toString()])
	)
	const res = await fetch(
		`${PCS_API_DOMAIN}/search?q=${encodeURIComponent(
			normalizedQuery
		)}&${urlParams.toString()}`
	)
	const data = await res.json()
	return data
}

type QueryHookOptions = CourseSearchOptions & { debounce?: number }

export const useCourseSearch = (
	defaultQuery?: string,
	options?: QueryHookOptions
) => {
	const [query, setQuery] = useState<string | undefined>(defaultQuery)
	const debouncedQuery = useDebouncedValue(query, options?.debounce ?? 100)
	const [status, setStatus] = useState<FetchStatus>(FetchStatus.IDLE)
	const [results, setResults] = useState<CourseSearchResult>()

	useEffect(() => {
		if (!debouncedQuery) return
		setStatus(FetchStatus.LOADING)
		;(async () => {
			try {
				const data = await fetchQuery(debouncedQuery, options)
				setResults(data)
				setStatus(FetchStatus.SUCCESS)
			} catch (error) {
				setStatus(FetchStatus.ERROR)
			}
		})()
	}, [debouncedQuery, options])

	return {
		query,
		debouncedQuery,
		setQuery,
		status,
		results,
	}
}
