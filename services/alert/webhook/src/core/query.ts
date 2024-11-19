import db, { and, eq, isNull } from "@pennlabs/pca-backend/db"
import { $registration } from "@pennlabs/pca-backend/db/schema"
import { $authUser, $section } from "@pennlabs/pca-backend/db/schema/course"

export const getRegisteredUsers = async (sectionId: string) => {
	const users = await db
		.select({
			pennkey: $authUser.username,
			email: $authUser.email,
		})
		.from($section)
		.where(eq($section.fullCode, sectionId))
		.innerJoin(
			$registration,
			and(
				eq($section.id, $registration.sectionId),
				isNull($registration.deletedAt)
			)
		)
		.innerJoin($authUser, eq($registration.userId, $authUser.id))
	return users
}
