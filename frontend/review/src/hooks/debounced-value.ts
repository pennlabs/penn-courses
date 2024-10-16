import { useEffect, useState } from "react"

export const useDebouncedState = <T>(
	initialValue: T,
	delay = 500
): [T, (value: T) => void] => {
	const [value, setValue] = useState(initialValue)
	const debouncedValue = useDebouncedValue(value, delay)
	return [debouncedValue, setValue]
}

export const useDebouncedValue = <T>(value: T, delay = 500): T => {
	const [debouncedValue, setDebouncedValue] = useState(value)
	useEffect(() => {
		const handler = setTimeout(() => {
			setDebouncedValue(value)
		}, delay)
		return () => {
			clearTimeout(handler)
		}
	}, [value, delay])
	return debouncedValue
}
