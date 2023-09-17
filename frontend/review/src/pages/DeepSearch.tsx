import React, { Component, useEffect, useState } from "react"
import Navbar from "../components/Navbar"
import DeepSearchBar from "../components/DeepSearch/DeepSearchBar"
import Footer from "../components/Footer"
import { ErrorBox } from "../components/common"
import { apiSearch } from "../utils/api"
import { useHistory } from "react-router-dom"

/**
 * Represents a course, instructor, or department review page.
 */
export const DeepSearch = () => {
	const [error, setError] = useState({ code: "", detail: "" })
	const [movedUp, setMovedUp] = useState(false)

	useEffect(() => {
		setMovedUp(true)
	}, [])

	if (error.code) {
		return (
			<div>
				<Navbar />
				<ErrorBox detail={error.detail}>{error.code}</ErrorBox>
				<Footer />
			</div>
		)
	}
	return (
		<div id="content">
			<DeepSearchBar
				style={{
					margin: "0 auto",
					transition: "margin 600ms",
					marginTop: movedUp ? "2rem" : "14rem",
				}}
			/>
			<Footer style={{ marginTop: 150 }} />
		</div>
	)
}
