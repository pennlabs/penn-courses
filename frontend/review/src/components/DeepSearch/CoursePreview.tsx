import React, { useMemo } from "react"
import { RatingBox } from "./RatingBox"
import styled from "styled-components"
import { Star } from "../common"
import { CodeDecoration } from "./CommonStyles"
import { Course } from "../../types/course"
import { useSearchContext } from "./SearchContext"
import { Link } from "react-router-dom"

export const PreviewWrapper = styled.div`
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

const Instructors = styled.div`
	font-style: italic;
`

const Top = styled.div`
	display: flex;
	flex-direction: row;
	align-items: center;
	gap: 0.5rem;
`

const Container = styled.div`
	display: flex;
	flex-direction: column;
`

const ScoreWrapper = styled.div`
	display: flex;
	flex-direction: row;
	padding-left: 0.5rem;
	border-left: 1px solid #e0e0e0;
`

const Description = styled.p`
	padding: 0.5rem;
	font-size: 14px;
	line-height: 20px;
	margin-top: 1rem;
`

export const CoursePreview: React.FC<{
	course: Course
	style?: React.CSSProperties
	onClick?: () => void
}> = ({ course, style, onClick }) => {
	const { query } = useSearchContext()

	const matchedDescription = useMemo(() => {
		if (!query) return [{ text: course.description, isMatch: false }]
		const matches = Array.from(
			course.description
				.toLowerCase()
				.matchAll(new RegExp(query.toLowerCase(), "gi"))
		)
		const splits = [
			[0, false],
			...matches.flatMap((m) => [
				[m.index!, true],
				[m.index! + m[0].length, false],
			]),
		] as [number, boolean][]
		const split = splits.map((i, j) => {
			const isMatch = i[1]
			const text = course.description.slice(
				i[0],
				splits[j + 1]?.[0] ?? course.description.length
			)
			return { text, isMatch }
		})
		return split
	}, [query])

	return (
		<Container style={style} onClick={onClick}>
			<Link
				to={`/course/${course.cleanCode}`}
				style={{
					color: "inherit",
					textDecoration: "none",
				}}>
				<div
					style={{
						display: "flex",
						flexDirection: "row",
						justifyContent: "space-between",
						alignItems: "center",
					}}>
					<div
						style={{
							display: "flex",
							flexDirection: "column",
							gap: ".5rem",
						}}>
						<Top>
							<div>
								<CodeDecoration>{course.code}</CodeDecoration>
								<span>{course.title}</span>
							</div>
							<Star isFilled={course.current} />
						</Top>
						{course.instructors?.length && (
							<Instructors>
								<span
									style={{
										fontWeight: "bold",
									}}>
									Most Recently:
								</span>
								<span>{course.instructors.join(", ")}</span>
							</Instructors>
						)}
					</div>
					<ScoreWrapper>
						<RatingBox rating={course.quality} label="Quality" />
						<RatingBox rating={course.work} label="Work" />
						<RatingBox rating={course.difficulty} label="Difficulty" />
					</ScoreWrapper>
				</div>
				<Description>
					{matchedDescription.map((m, i) => (
						<span
							key={i}
							style={{
								color: m.isMatch ? "white" : "inherit",
								backgroundColor: m.isMatch ? "#85b8ba" : "transparent",
								fontWeight: m.isMatch ? 900 : "normal",
							}}>
							{m.text}
						</span>
					))}
				</Description>
			</Link>
		</Container>
	)
}
