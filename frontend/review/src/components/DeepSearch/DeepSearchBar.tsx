import React, { PropsWithChildren, useMemo, useState } from "react"
import { useHistory } from "react-router-dom"
import { CoursePreview } from "./CoursePreview"
import Slider from "rc-slider"
import "rc-slider/assets/index.css"
import styled from "styled-components"
import { CodeDecoration } from "./CommonStyles"
import { CourseSearchOptions } from "../../hooks/course-search"

const PCAGreen = (opacity = 1) => `rgba(90, 144, 147, ${opacity})`

const FlexRow = styled.div`
	display: flex;
	flex-direction: row;
	align-items: center;
`

const ConstWidthText = styled.div`
	width: 100px;
`

const SearchWrapper = styled.div`
	margin: 0 auto;
	position: relative;
	display: inline-block;
`
/**
 * The search bar that appears on the homepage and navigation bar.
 */
const SearchBar = styled.div`
	height: 4rem;
	width: calc(100vw - 60px);
	max-width: 800px;

	overflow: hidden;

	border-radius: 8px;
	box-shadow: rgba(0, 0, 0, 0.07) 0px 2px 14px 0px;
	background-color: #ffffff;

	border: solid 1px #e6e6e6;
	margin: 0 auto;
	padding: 12px;

	display: flex;
	justify-content: space-between;
	align-items: center;
`
const SearchInput = styled.input`
	height: 100%;
	width: 90%;
	border: none;
	flex: 1;
	font-size: 18px;
	color: rgb(178, 178, 178);
	box-sizing: border-box;
	white-space: nowrap;
`
const DropDownWrapper = styled.div`
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
`
const SliderDropDown = styled.div`
	position: absolute;
	top: 5rem;
	right: 0;
	z-index: 20;

	display: grid;
	grid-template-columns: 1fr;
	gap: 24px;

	padding: 24px 24px;

	background-color: white;
	border-radius: 8px;

	box-shadow: 0 2px 3px rgb(10 10 10 / 10%), 0 0 0 1px rgb(10 10 10 / 10%);
	box-shadow: 0 0 25px 0 rgb(0 0 0 / 10%);
`

const RANGE_PROPS: React.ComponentProps<typeof Slider> = {
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
	handleStyle: [{ borderColor: "#85b8ba" }, { borderColor: "#85b8ba" }],
	style: {
		width: 200,
	},
}

type DeepSearchBarProps = {
	initialSearchValue?: string
	style?: React.CSSProperties
	query?: string
	onQueryChange?: (query: string) => void
	queryOptions: CourseSearchOptions
	onQueryOptionsChange?: (queryOptions: CourseSearchOptions) => void
}

const DeepSearchBar: React.FC<DeepSearchBarProps> = (props) => {
	const [query, setQuery] = useState(props.initialSearchValue ?? "")

	const [showOptions, setShowOptions] = useState(false)
	const [queryOptions, setQueryOptions] = useState<CourseSearchOptions>(
		props.queryOptions
	)

	return (
		<SearchWrapper>
			<SearchBar>
				<SearchInput
					placeholder="Search for anything..."
					value={query}
					onChange={(e) => {
						setQuery(e.target.value)
						props.onQueryChange?.(e.target.value)
					}}
					autoFocus
				/>
				<DropDownWrapper id="filter-dropdown">
					<button
						onClick={() => setShowOptions(!showOptions)}
						style={{
							color: PCAGreen(1),
							cursor: "pointer",
							display: "flex",
							alignItems: "center",
							justifyContent: "center",
							background: "none",
							border: "none",
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
				</DropDownWrapper>
			</SearchBar>
			<SliderDropDown
				style={{
					visibility: showOptions ? "visible" : "hidden",
				}}>
				<FlexRow>
					<ConstWidthText>Quality</ConstWidthText>
					<Slider
						value={[queryOptions.qualityLow, queryOptions.qualityHigh]}
						onChange={([low, high]: any) => {
							const newOpts = {
								...queryOptions,
								qualityLow: low,
								qualityHigh: high,
							}
							setQueryOptions(newOpts)
							props.onQueryOptionsChange?.(newOpts)
						}}
						{...RANGE_PROPS}
					/>
				</FlexRow>
				<FlexRow>
					<ConstWidthText>Difficulty</ConstWidthText>
					<Slider
						value={[queryOptions.difficultyLow, queryOptions.difficultyHigh]}
						onChange={([low, high]: any) => {
							const newOpts = {
								...queryOptions,
								difficultyLow: low,
								difficultyHigh: high,
							}
							setQueryOptions(newOpts)
							props.onQueryOptionsChange?.(newOpts)
						}}
						{...RANGE_PROPS}
					/>
				</FlexRow>
				<FlexRow>
					<ConstWidthText>Work</ConstWidthText>
					<Slider
						value={[queryOptions.workLow, queryOptions.workHigh]}
						onChange={([low, high]: any) => {
							const newOpts = {
								...queryOptions,
								workLow: low,
								workHigh: high,
							}
							setQueryOptions(newOpts)
							props.onQueryOptionsChange?.(newOpts)
						}}
						{...RANGE_PROPS}
					/>
				</FlexRow>
			</SliderDropDown>
		</SearchWrapper>
	)
}

export default DeepSearchBar
