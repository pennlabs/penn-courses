import { bigint, index, pgTable, timestamp, uuid } from 'drizzle-orm/pg-core'

import { $authUser, $section } from '@/core/db/schema/course'

export const $registration = pgTable(
	'alert_v2_registration',
	{
		id: uuid('id').primaryKey().defaultRandom(),
		sectionId: bigint('section_id', {
			mode: 'bigint',
		})
			.notNull()
			.references(() => $section.id),
		userId: bigint('user_id', { mode: 'bigint' })
			.notNull()
			.references(() => $authUser.id),
		createdAt: timestamp('created_at').defaultNow(),
		deletedAt: timestamp('deleted_at'),
	},
	t => ({
		indexOnSection: index('alert_v2_registration_section_id_idx').onOnly(
			t.sectionId,
		),
		indexOnUser: index('alert_v2_registration_user_id_idx').onOnly(t.userId),
	}),
)
