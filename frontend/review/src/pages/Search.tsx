import React, { useState } from "react"
import DeepSearchBar from "../components/DeepSearch/DeepSearchBar"
import Footer from "../components/Footer"
import { useHistory, useLocation } from "react-router-dom"
import { CourseSearchOptions, useCourseSearch } from "../hooks/course-search"
import styled from "styled-components"
import SearchBar from "../components/SearchBar"
import {
	CoursePreview,
	PreviewWrapper,
} from "../components/DeepSearch/CoursePreview"
const PCAGreen = (opacity = 1) => `rgba(90, 144, 147, ${opacity})`

enum SearchMode {
	COURSE_CODE,
	KEYWORD,
}

const DEFAULT_OPTIONS: CourseSearchOptions = {
	workLow: 0,
	workHigh: 4,
	difficultyLow: 0,
	difficultyHigh: 4,
	qualityLow: 0,
	qualityHigh: 4,
}

const Root = styled.main`
	padding: 30px 15px;
	min-height: 100vh;
`

const SearchModeSelectorRoot = styled.div`
	border-radius: 8px;
	box-shadow: rgba(0, 0, 0, 0.07) 0px 2px 14px 0px;
	background-color: #ffffff;

	border: solid 1px #e6e6e6;
	margin: 0 auto;
	padding: 8px 12px;

	display: flex;
	justify-content: space-between;
	align-items: center;
`

const SearchModeSelectorOption = styled.div<{
	active: boolean
}>`
	&:not(:last-child) {
		margin-right: 8px;
	}

	border-radius: 4px;
	padding: 8px;
	cursor: pointer;
	transition: 0.2s;
	background: ${(props) => (props.active ? PCAGreen(0.8) : "#ffffff")};
	color: ${(props) => (props.active ? "#ffffff" : PCAGreen(0.8))};
`

/** */

const SearchModeSelector: React.FC<{
	style?: React.CSSProperties
	value: SearchMode
	onChange: (value: SearchMode) => void
}> = ({ style, value, onChange }) => {
	return (
		<SearchModeSelectorRoot style={style}>
			<SearchModeSelectorOption
				active={value === SearchMode.COURSE_CODE}
				onClick={() => onChange(SearchMode.COURSE_CODE)}>
				{" "}
				Course Code
			</SearchModeSelectorOption>
			<SearchModeSelectorOption
				active={value === SearchMode.KEYWORD}
				onClick={() => onChange(SearchMode.KEYWORD)}>
				{" "}
				Keyword
			</SearchModeSelectorOption>
		</SearchModeSelectorRoot>
	)
}

export const Search = () => {
	const history = useHistory()
	const location = useLocation()

	const search = new URLSearchParams(location.search).get("query") ?? ""

	const [searchMode, setSearchMode] = useState<SearchMode>(
		SearchMode.COURSE_CODE
	)

	const [queryOptions, setQueryOptions] = useState<CourseSearchOptions>(
		DEFAULT_OPTIONS
	)

	const { query, setQuery, results } = useCourseSearch(
		search,
		queryOptions
	)

	return (
		<Root>
			<div id="title">
				<img
					src="/static/image/logo.png"
					alt="Penn Course Review"
					onClick={() => history.push("/")}
				/>{" "}
				<span className="title-text">Penn Course Review</span>
			</div>
			<div
				style={{
					display: "flex",
					flexDirection: "column",
					alignItems: "center",
				}}>
				{searchMode === SearchMode.COURSE_CODE && <SearchBar isTitle />}
				{searchMode === SearchMode.KEYWORD && (
					<DeepSearchBar
						initialSearchValue={search}
						query={query}
						onQueryChange={(query) => {
							const url = new URL(window.location.href)
							url.searchParams.set("query", query)
							history.replace({
								pathname: location.pathname,
								search: url.search,
							})
							setQuery(query)
						}}
						queryOptions={queryOptions}
						onQueryOptionsChange={setQueryOptions}
					/>
				)}
				<SearchModeSelector
					style={{
						marginTop: 20,
					}}
					value={searchMode}
					onChange={(v) => setSearchMode(v)}
				/>
			</div>
			<div id="keyword-results">
				{searchMode === SearchMode.KEYWORD && results?.Courses.length ? (
					<PreviewWrapper
						style={{
							maxWidth: 800,
							margin: "24px auto",
						}}>
						{results?.Courses.map((course) => (
							<CoursePreview key={course.code} course={course} />
						))}
					</PreviewWrapper>
				) : null}
			</div>
			<Footer style={{ marginTop: 150 }} />
		</Root>
	)
}
