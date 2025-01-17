import { getRegisteredUsers } from "@/core/query"
import { expect, test } from "vitest"

test("Query returns users", async () => {
	const users = await getRegisteredUsers("CIS-1200-001")
	expect(users).toBeDefined()
})
