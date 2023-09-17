import React from "react"
import { getColor } from "../../utils/helpers"
import styled from "styled-components"

const Label = styled.p`
	font-size: 15px;
	letter-spacing: -0.3px;
	margin-top: 16px;
`

const Score = styled.p`
	color: white;
	margin-top: 15px;
	font-size: 20px;
`

const Box = styled.div`
	margin-left: 5px;
	margin-right: 5px;
	height: 60px;
	width: 60px;
	border-radius: 4px;
	text-align: center;
`

/**
 * The rating box that display the course ratings out of 4 (ex: 3.7).
 */
export function RatingBox({ rating, label }) {
	return (
		<Box className={`scorebox ${getColor(rating)}`}>
			<Score>
				{typeof rating !== "number" || isNaN(rating)
					? "N/A"
					: rating.toFixed(1)}
			</Score>
			<Label>{label}</Label>
		</Box>
	)
}
