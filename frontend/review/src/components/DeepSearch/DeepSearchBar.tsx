import React, { PropsWithChildren, useEffect, useMemo, useState } from "react"
import { useHistory } from "react-router-dom"
import { API_DOMAIN } from "../../utils/api"
import { CoursePreview } from "./CoursePreview"
import { debounce } from "lodash"
import { Range } from "rc-slider"
import "rc-slider/assets/index.css"
import styled from "styled-components"
import { RatingBox } from "./RatingBox"
import { CodeDecoration } from "./CommonStyles"
import { useDebouncedValue } from "../../hooks/debounced-value"
import { Course } from "../../types/course"
import { Department } from "../../types/department"
import { Instructor } from "../../types/instructor"
import SearchContextProvider from "./SearchContext"

const PCAGreen = (opacity = 1) => `rgba(90, 144, 147, ${opacity})`

const FlexRow = styled.div`
	display: flex;
	flex-direction: row;
	align-items: center;
`

const ConstWidthText = styled.div`
	width: 100px;
`

const Wrapper = styled.div`
	max-width: 768px;
	width: "100%";
	&:hover {
		cursor: pointer;
	}
`

const SearchWrapper = styled.div`
	// wrapper for searchbar + results
	width: 100%;
	display: flex;
	justify-content: center;
	flex-direction: column;
	gap: 5;
`

const Search = styled.div`
	margin: 0 auto;
	width: 100%;
	height: 4rem;
	display: flex;
	flex-direction: row;
	align-items: center;
	gap: 0.5rem;
	box-shadow: 0 0 40px -12px rgb(0 0 0 / 0.25);
	padding: 1rem;
	background-color: #ffffff;
	border-radius: 5px;
`

const SliderDropDown = styled.div`
	display: flex;
	flex-direction: column;
	gap: 1.5rem;
	width: 50%;
	margin-top: 1.5rem;
	right: -1rem;
	position: absolute;
	top: 100%;
	z-index: 20;
	background-color: white;
	border-radius: 4px;
	box-shadow: 0 2px 3px rgb(10 10 10 / 10%), 0 0 0 1px rgb(10 10 10 / 10%);
	padding: 1rem;
	padding-right: 1.25rem;
	padding-bottom: 1.6rem;
	width: 20rem;
	box-shadow: 0 0 25px 0 rgb(0 0 0 / 10%);
`

const SearchInput = styled.input`
	height: 100%;
	border: none;
	flex: 1;
	border-bottom: 2px solid ${PCAGreen(0.25)};
	&:focus {
		outline: none;
		border-bottom: 2px solid ${PCAGreen(0.75)};
	}
	::placeholder,
	::-webkit-input-placeholder {
		font-style: italic;
	}
`

const PreviewWrapper = styled.div`
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	background-color: white;
	padding-top: 1rem;
	padding-bottom: 1rem;
	padding-left: 0.75rem;
	padding-right: 0.75rem;
	box-shadow: 0 0 22px -12px rgb(0 0 0 / 0.25);
	margin-bottom: 2rem;
	border-radius: 5px;
	& > div + div {
		border-top: 1px solid #e0e0e0;
		padding-top: 1.5rem;
	}
`

const ResultCategory = styled.div`
	// Courses, Departments, Instructors
	margin-top: 1.5rem;
	margin-bottom: 0.75rem;
	width: 100%;
	color: #aaa;
	font-size: 14px;
	font-weight: bold;
	letter-spacing: -0.25px;
	border-bottom: 1px solid #aaa;
	display: flex;
	flex-direction: row;
	justify-content: space-between;
`

const DepartmentPreviewComponent = ({
	department: { code, name, quality, work, difficulty },
	onClick,
}) => (
	<FlexRow
		style={{
			fontSize: "1rem",
			justifyContent: "space-between",
		}}
		onClick={onClick}>
		<div>
			<CodeDecoration
				style={{
					backgroundColor: "lavender",
				}}
				dangerouslySetInnerHTML={{ __html: code }}
			/>{" "}
			<span dangerouslySetInnerHTML={{ __html: name }} />
		</div>
	</FlexRow>
)

const ResultCategoryComponent: React.FC<PropsWithChildren<{
	category: string
}>> = ({ category, children }) => {
	const [folded, setFolded] = useState(false)
	return (
		<>
			<ResultCategory onClick={() => setFolded(!folded)}>
				<span>{category}</span>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 512 512"
					style={{
						height: "1rem",
					}}>
					<path
						key={String(folded)}
						fill="none"
						stroke="currentColor"
						strokeLinecap="square"
						strokeMiterlimit="10"
						strokeWidth="48"
						d={folded ? "M328 112L184 256l144 144" : "M112 184l144 144 144-144"}
					/>
				</svg>
			</ResultCategory>
			{!folded && children}
		</>
	)
}

enum FetchStatus {
	IDLE,
	LOADING,
	SUCCESS,
	ERROR,
}

type QueryResult = {
	Courses: Course[]
	Departments: Department[]
	Instructors: Instructor[]
}
type QueryOptions = {
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
	options: QueryOptions = {
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
		`${API_DOMAIN}/api/review/search?q=${encodeURIComponent(
			normalizedQuery
		)}&${urlParams.toString()}`
	)
	const data = await res.json()
	return data
}

type QueryHookOptions = QueryOptions & { debounce?: number }

const useQuery = (defaultQuery?: string, options?: QueryHookOptions) => {
	const [query, setQuery] = useState<string | undefined>(defaultQuery)
	const debouncedQuery = useDebouncedValue(query, options?.debounce ?? 100)

	const [status, setStatus] = useState<FetchStatus>(FetchStatus.IDLE)
	const [results, setResults] = useState<QueryResult>()

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

type DeepSearchBarProps = {
	initialSearchValue?: string
	style?: React.CSSProperties
}

const DeepSearchBar: React.FC<DeepSearchBarProps> = (props) => {
	const history = useHistory()
	const [showFilters, setShowFilters] = useState(false)

	const [queryOptions, setQueryOptions] = useState<QueryOptions>({
		workLow: 0,
		workHigh: 4,
		difficultyLow: 0,
		difficultyHigh: 4,
		qualityLow: 0,
		qualityHigh: 4,
	})

	const {
		query,
		debouncedQuery,
		results,
		setQuery,
		status: fetchStatus,
	} = useQuery(props.initialSearchValue, queryOptions)

	const coursePreviews = results?.Courses.map((course, idx) => (
		<CoursePreview
			key={idx}
			style={{}}
			onClick={() => history.push(`/course/${course.cleanCode}`)}
			course={course}
		/>
	))

	const rangeProps = useMemo(
		() => ({
			min: 0,
			max: 4,
			step: 0.1,
			marks: {
				0: { style: {}, label: "0" },
				4: { style: {}, label: "4" },
			},
			trackStyle: [
				{
					backgroundColor: "#85b8ba",
				},
			],
			handleStyle: [{ borderColor: "#85b8ba" }],
		}),
		[]
	)

	return (
		<SearchContextProvider query={debouncedQuery}>
			<Wrapper style={props.style}>
				<SearchWrapper>
					<Search>
						<img
							src="/static/image/logo.png"
							alt="Penn Course Review"
							style={{
								height: "100%",
							}}
							onClick={() => history.push("/")}
						/>{" "}
						<SearchInput
							placeholder="Search for anything..."
							value={query}
							onChange={(e) => {
								if (e.target.value.length === 0) {
									return history.push("/", { animate: true })
								}
								setQuery(e.target.value)
							}}
							autoFocus
						/>
						<div
							id="filter-dropdown"
							style={{
								position: "relative",
							}}>
							<button
								className="btn btn-sm btn-outline-primary"
								onClick={() => setShowFilters(!showFilters)}
								style={{
									color: PCAGreen(0.5),
								}}>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									style={{
										height: "1.5rem",
										width: "1.5rem",
									}}
									viewBox="0 0 512 512"
									stroke="currentColor"
									fill="currentColor">
									<path d="M381.25 112a48 48 0 00-90.5 0H48v32h242.75a48 48 0 0090.5 0H464v-32zM176 208a48.09 48.09 0 00-45.25 32H48v32h82.75a48 48 0 0090.5 0H464v-32H221.25A48.09 48.09 0 00176 208zM336 336a48.09 48.09 0 00-45.25 32H48v32h242.75a48 48 0 0090.5 0H464v-32h-82.75A48.09 48.09 0 00336 336z" />
								</svg>
							</button>
							<SliderDropDown
								style={{
									visibility: showFilters ? "visible" : "hidden",
								}}>
								<FlexRow>
									<ConstWidthText>Quality</ConstWidthText>
									<Range
										value={[queryOptions.qualityLow, queryOptions.qualityHigh]}
										onChange={([low, high]) =>
											setQueryOptions({
												...queryOptions,
												qualityLow: low,
												qualityHigh: high,
											})
										}
										{...rangeProps}
									/>
								</FlexRow>
								<FlexRow>
									<ConstWidthText>Difficulty</ConstWidthText>
									<Range
										value={[
											queryOptions.difficultyLow,
											queryOptions.difficultyHigh,
										]}
										onChange={([low, high]) =>
											setQueryOptions({
												...queryOptions,
												difficultyLow: low,
												difficultyHigh: high,
											})
										}
										{...rangeProps}
									/>
								</FlexRow>
								<FlexRow>
									<ConstWidthText>Work</ConstWidthText>
									<Range
										value={[queryOptions.workLow, queryOptions.workHigh]}
										onChange={([low, high]) =>
											setQueryOptions({
												...queryOptions,
												workLow: low,
												workHigh: high,
											})
										}
										{...rangeProps}
									/>
								</FlexRow>
							</SliderDropDown>
						</div>
					</Search>
				</SearchWrapper>
				{(coursePreviews?.length ?? 0) > 0 && (
					<PreviewWrapper
						style={{
							marginTop: "1rem",
						}}>
						{coursePreviews}
					</PreviewWrapper>
				)}
			</Wrapper>
		</SearchContextProvider>
	)
}

export default DeepSearchBar
