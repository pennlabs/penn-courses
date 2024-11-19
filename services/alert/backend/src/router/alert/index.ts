import { and, desc, eq, inArray, isNull } from 'drizzle-orm'
import { z } from 'zod'

import db from '@/core/db'
import { $notificationHistory, $registration } from '@/core/db/schema'
import { $course, $section } from '@/core/db/schema/course'
import { ENV } from '@/core/env'
import { router } from '@/core/trpc'
import authProcedure from '@/core/trpc/procedures/auth.procedure'

export const alertRouter = router({
	register: authProcedure
		.input(
			z.object({
				sectionCodes: z.array(z.string()),
			}),
		)
		.mutation(
			async ({
				ctx: {
					user: { pennid },
				},
				input: { sectionCodes },
			}) => {
				const sections = await db
					.selectDistinctOn([$section.id], {
						id: $section.id,
						fullCode: $section.fullCode,
					})
					.from($section)
					.where(inArray($section.fullCode, sectionCodes))
					.innerJoin(
						$course,
						and(
							eq($section.courseId, $course.id),
							eq($course.semester, ENV.CURRENT_SEMESTER),
						),
					)
				const insertion: (typeof $registration.$inferInsert)[] = sections.map(
					section => ({
						sectionId: section.id,
						userId: BigInt(pennid),
					}),
				)
				const { insertedSectionIds, duplicateSectionIds } =
					await db.transaction(async tx => {
						const duplicates = await tx
							.select({
								sectionId: $registration.sectionId,
							})
							.from($registration)
							.where(
								and(
									inArray(
										$registration.sectionId,
										sections.map(s => s.id),
									),
									eq($registration.userId, BigInt(pennid)),
									isNull($registration.deletedAt),
								),
							)
						const duplicateSectionIds = new Set(
							duplicates.map(d => d.sectionId),
						)
						const toInsert = insertion.filter(
							v => !duplicateSectionIds.has(v.sectionId),
						)
						if (toInsert.length === 0) {
							return {
								insertedSectionIds: new Set(),
								duplicateSectionIds,
							}
						}
						const inserted = await db
							.insert($registration)
							.values(toInsert)
							.returning({
								sectionId: $registration.sectionId,
							})
						const insertedSectionIds = new Set(inserted.map(i => i.sectionId))
						return {
							insertedSectionIds,
							duplicateSectionIds,
						}
					})
				return {
					insertedSections: sections
						.filter(s => insertedSectionIds.has(s.id))
						.map(s => s.fullCode),
					duplicateSections: sections
						.filter(s => duplicateSectionIds.has(s.id))
						.map(s => s.fullCode),
				}
			},
		),
	unregister: authProcedure
		.input(
			z.object({
				registrationIds: z.array(z.string()),
			}),
		)
		.mutation(
			async ({
				ctx: {
					user: { pennid },
				},
				input: { registrationIds },
			}) => {
				const deleted = await db
					.update($registration)
					.set({
						deletedAt: new Date(),
					})
					.where(
						and(
							inArray($registration.id, registrationIds),
							eq($registration.userId, BigInt(pennid)),
						),
					)
					.returning({
						id: $registration.id,
						sectionId: $registration.sectionId,
					})
				return deleted
			},
		),
	list: authProcedure.query(async ({ ctx: { user } }) => {
		const registrations = await db
			.select({
				id: $registration.id,
				section: {
					id: $section.id,
					code: $section.fullCode,
					status: $section.status,
				},
				course: {
					code: $course.fullCode,
					title: $course.title,
					semester: $course.semester,
				},
				createdAt: $registration.createdAt,
				deletedAt: $registration.deletedAt,
			})
			.from($registration)
			.where(eq($registration.userId, BigInt(user.pennid)))
			.innerJoin($section, eq($registration.sectionId, $section.id))
			.innerJoin($course, eq($section.courseId, $course.id))
			.orderBy(desc($registration.createdAt))
		return registrations
	}),
	history: authProcedure
		.input(
			z.object({
				limit: z.number().default(10),
				cursor: z.number().default(0),
			}),
		)
		.query(async ({ ctx: { user }, input: { limit, cursor } }) => {
			const history = await db
				.select({
					id: $notificationHistory.id,
					section: {
						id: $section.id,
						code: $section.fullCode,
						status: $notificationHistory.sectionStatus,
					},
					status: $notificationHistory.status,
					notifiedTo: $notificationHistory.notifiedTo,
					timestamp: $notificationHistory.createdAt,
				})
				.from($registration)
				.where(eq($registration.userId, BigInt(user.pennid)))
				.rightJoin(
					$notificationHistory,
					eq($registration.id, $notificationHistory.registrationId),
				)
				.innerJoin($section, eq($registration.sectionId, $section.id))
				.orderBy(desc($notificationHistory.createdAt))
				.limit(limit)
				.offset(cursor)
			return history
		}),
})
