import { pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core'

import { $registration } from '@/core/db/schema/alert/registration.model'

export const $notificationHistory = pgTable('alert_v2_notification_history', {
	id: uuid('id').primaryKey().defaultRandom(),
	registrationId: uuid('registration_id')
		.notNull()
		.references(() => $registration.id),
	sectionStatus: text('section_status', {
		enum: ['OPEN', 'CLOSED'],
	}).notNull(),
	status: text('status', {
		enum: ['DELIVERED', 'UNDELIVERED', 'ERROR'],
	}).notNull(),
	notifiedTo: text('notified_to').notNull(),
	createdAt: timestamp('created_at'),
})
