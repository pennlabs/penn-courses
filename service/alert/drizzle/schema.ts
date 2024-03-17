import {
	pgTable,
	index,
	foreignKey,
	serial,
	varchar,
	timestamp,
	doublePrecision,
	boolean,
	integer,
	uniqueIndex,
	bigserial,
	bigint,
	unique,
} from "drizzle-orm/pg-core"

export const $demandDistributionEstimate = pgTable(
	"alert_pcademanddistributionestimate",
	{
		id: serial("id").primaryKey().notNull(),
		semester: varchar("semester", { length: 5 }).notNull(),
		createdAt: timestamp("created_at", {
			withTimezone: true,
			mode: "string",
		}).notNull(),
		percentThroughAddDropPeriod: doublePrecision(
			"percent_through_add_drop_period"
		).notNull(),
		inAddDropPeriod: boolean("in_add_drop_period").notNull(),
		highestDemandSectionVolume: integer(
			"highest_demand_section_volume"
		).notNull(),
		lowestDemandSectionVolume: integer(
			"lowest_demand_section_volume"
		).notNull(),
		highestDemandSectionId: integer("highest_demand_section_id").notNull(),
		lowestDemandSectionId: integer("lowest_demand_section_id").notNull(),
		csprdvLognormParamLoc: doublePrecision("csprdv_lognorm_param_loc"),
		csprdvLognormParamScale: doublePrecision("csprdv_lognorm_param_scale"),
		csprdvLognormParamShape: doublePrecision("csprdv_lognorm_param_shape"),
		csrdvFracZero: doublePrecision("csrdv_frac_zero"),
	},
	(table) => {
		return {
			semester37849A16: index(
				"alert_pcademanddistributionestimate_semester_37849a16"
			).on(table.semester),
			semester37849A16Like: index(
				"alert_pcademanddistributionestimate_semester_37849a16_like"
			).on(table.semester),
			createdAt5410C834: index(
				"alert_pcademanddistributionestimate_created_at_5410c834"
			).on(table.createdAt),
			alertPcademanddistributioHighestDemandSectionId57Bb8642: index(
				"alert_pcademanddistributio_highest_demand_section_id_57bb8642"
			).on(table.highestDemandSectionId),
			alertPcademanddistributioLowestDemandSectionId5C0092E2: index(
				"alert_pcademanddistributio_lowest_demand_section_id_5c0092e2"
			).on(table.lowestDemandSectionId),
		}
	}
)

export const $registration = pgTable(
	"alert_registration",
	{
		id: bigserial("id", { mode: "bigint" }).primaryKey().notNull(),
		createdAt: timestamp("created_at", {
			withTimezone: true,
			mode: "string",
		}).notNull(),
		updatedAt: timestamp("updated_at", {
			withTimezone: true,
			mode: "string",
		}).notNull(),
		email: varchar("email", { length: 254 }),
		phone: varchar("phone", { length: 100 }),
		notificationSent: boolean("notification_sent").notNull(),
		notificationSentAt: timestamp("notification_sent_at", {
			withTimezone: true,
			mode: "string",
		}),
		notificationSentBy: varchar("notification_sent_by", {
			length: 16,
		}).notNull(),
		// You can use { mode: "bigint" } if numbers are exceeding js number limitations
		resubscribedFromId: bigint("resubscribed_from_id", { mode: "number" }),
		// You can use { mode: "bigint" } if numbers are exceeding js number limitations
		sectionId: bigint("section_id", { mode: "number" }).notNull(),
		// You can use { mode: "bigint" } if numbers are exceeding js number limitations
		apiKeyId: bigint("api_key_id", { mode: "number" }),
		source: varchar("source", { length: 16 }).notNull(),
		deleted: boolean("deleted").notNull(),
		deletedAt: timestamp("deleted_at", { withTimezone: true, mode: "string" }),
		autoResubscribe: boolean("auto_resubscribe").notNull(),
		// You can use { mode: "bigint" } if numbers are exceeding js number limitations
		userId: bigint("user_id", { mode: "number" }),
		originalCreatedAt: timestamp("original_created_at", {
			withTimezone: true,
			mode: "string",
		}),
		cancelled: boolean("cancelled").notNull(),
		cancelledAt: timestamp("cancelled_at", {
			withTimezone: true,
			mode: "string",
		}),
		closeNotification: boolean("close_notification").notNull(),
		closeNotificationSent: boolean("close_notification_sent").notNull(),
		closeNotificationSentAt: timestamp("close_notification_sent_at", {
			withTimezone: true,
			mode: "string",
		}),
		closeNotificationSentBy: varchar("close_notification_sent_by", {
			length: 16,
		}).notNull(),
		headRegistrationId: integer("head_registration_id").notNull(),
	},
	(table) => {
		return {
			idx24879ResubscribedFromId: uniqueIndex(
				"idx_24879_resubscribed_from_id"
			).on(table.resubscribedFromId),
			idx24879AlertRegistrationSectionId530B9BafFkCoursesSec: index(
				"idx_24879_alert_registration_section_id_530b9baf_fk_courses_sec"
			).on(table.sectionId),
			idx24879AlertRegistrationApiKeyId3B2B38C6FkCoursesApi: index(
				"idx_24879_alert_registration_api_key_id_3b2b38c6_fk_courses_api"
			).on(table.apiKeyId),
			idx24879AlertRegistrationUserIdC35D7D06FkAuthUserId: index(
				"idx_24879_alert_registration_user_id_c35d7d06_fk_auth_user_id"
			).on(table.userId),
			headRegistrationId2E55Fa08: index(
				"alert_registration_head_registration_id_2e55fa08"
			).on(table.headRegistrationId),
			alertRegistrationHeadRegistrationId2E55Fa08FkAlertReg: foreignKey({
				columns: [table.headRegistrationId],
				foreignColumns: [table.id],
				name: "alert_registration_head_registration_id_2e55fa08_fk_alert_reg",
			}),
			alertRegistrationResubscribedFromIdF3055D31FkAlertReg: foreignKey({
				columns: [table.resubscribedFromId],
				foreignColumns: [table.id],
				name: "alert_registration_resubscribed_from_id_f3055d31_fk_alert_reg",
			}),
		}
	}
)

export const $addDropPeriod = pgTable(
	"alert_adddropperiod",
	{
		id: serial("id").primaryKey().notNull(),
		semester: varchar("semester", { length: 5 }).notNull(),
		start: timestamp("start", { withTimezone: true, mode: "string" }),
		end: timestamp("end", { withTimezone: true, mode: "string" }),
		estimatedStart: timestamp("estimated_start", {
			withTimezone: true,
			mode: "string",
		}),
		estimatedEnd: timestamp("estimated_end", {
			withTimezone: true,
			mode: "string",
		}),
	},
	(table) => {
		return {
			semester0552C5EbLike: index(
				"alert_adddropperiod_semester_0552c5eb_like"
			).on(table.semester),
			alertAdddropperiodSemesterKey: unique(
				"alert_adddropperiod_semester_key"
			).on(table.semester),
		}
	}
)
