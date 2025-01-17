import {
	bigint,
	bigserial,
	boolean,
	integer,
	numeric,
	pgTable,
	text,
	timestamp,
	varchar,
} from 'drizzle-orm/pg-core'

export const $course = pgTable('courses_course', {
	id: bigserial('id', { mode: 'bigint' }).primaryKey().notNull(),
	createdAt: timestamp('created_at', {
		withTimezone: true,
		mode: 'string',
	}).notNull(),
	updatedAt: timestamp('updated_at', {
		withTimezone: true,
		mode: 'string',
	}).notNull(),
	// You can use { mode: "bigint" } if numbers are exceeding js number limitations
	departmentId: bigint('department_id', { mode: 'number' }).notNull(),
	code: varchar('code', { length: 8 }).notNull(),
	semester: varchar('semester', { length: 5 }).notNull(),
	title: text('title').notNull(),
	description: text('description').notNull(),
	// You can use { mode: "bigint" } if numbers are exceeding js number limitations
	primaryListingId: bigint('primary_listing_id', {
		mode: 'number',
	}).notNull(),
	fullCode: varchar('full_code', { length: 16 }).notNull(),
	prerequisites: text('prerequisites').notNull(),
	numActivities: integer('num_activities').notNull(),
	topicId: integer('topic_id'),
	syllabusUrl: text('syllabus_url'),
	manuallySetParentCourse: boolean('manually_set_parent_course').notNull(),
	parentCourseId: integer('parent_course_id'),
	credits: numeric('credits', { precision: 4, scale: 2 }),
})
