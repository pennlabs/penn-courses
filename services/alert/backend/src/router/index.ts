import { z } from 'zod'

import db, { sql } from '@/core/db'
import { $course } from '@/core/db/schema/course'
import { procedure, router } from '@/core/trpc'
import { alertRouter } from '@/router/alert'
import { courseRouter } from '@/router/course'

const appRouter = router({
	alert: alertRouter,
	course: courseRouter,
	echo: procedure.input(z.any()).query(async ({ input }) => input),
	health: procedure.query(async () => ({ ok: true })),
	databaseCheck: procedure.query(async () => {
		const [courses] = await db
			.select({
				count: sql`COUNT(*)`.mapWith(Number),
			})
			.from($course)
		return {
			courses: courses.count,
		}
	}),
})

export default appRouter
export type AppRouter = typeof appRouter
