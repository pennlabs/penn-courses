import { Nullable } from "./utils"

export type Course = {
	code: string
	title: string
	description: string
	semester: string
	quality: Nullable<number>
	work: Nullable<number>
	difficulty: Nullable<number>
	current: boolean
	instructors: string[]
	cleanCode: string
}
