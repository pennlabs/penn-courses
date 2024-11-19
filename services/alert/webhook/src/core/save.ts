import db, { eq, and } from '@pennlabs/pca-backend/db'
import {
	$section,
	$statusUpdate,
	$course,
} from '@pennlabs/pca-backend/db/schema/course'
import { Status, type WebhookPayload } from '@/types/alert'
import { ENV } from '@/core/env'

export const updateCourseStatus = async (
	payload: WebhookPayload,
	requestBody: string,
) => {
	const sectionQuery = await db
		.select({
			id: $section.id,
			status: $section.status,
		})
		.from($section)
		.where(
			and(
				eq($section.fullCode, payload.section_id_normalized),
				eq($course.semester, ENV.CURRENT_SEMESTER),
			),
		)
		.innerJoin($course, eq($section.courseId, $course.id))
	const previousStatus = sectionQuery[0]?.status
	const sectionId = sectionQuery[0]?.id
	const typedPreviousStatus = Status[previousStatus as keyof typeof Status]
	if (typedPreviousStatus !== payload.previous_status) {
		return false
	}
	await db.transaction(async tx => {
		await tx
			.update($section)
			.set({
				status: payload.status,
			})
			.where(eq($section.id, sectionId))
		await tx.insert($statusUpdate).values({
			oldStatus: payload.previous_status,
			newStatus: payload.status,
			createdAt: new Date().toISOString(),
			alertSent: true,
			requestBody: requestBody,
			sectionId: Number(sectionId),
			inAddDropPeriod: false,
		})
	})
	return true
}
