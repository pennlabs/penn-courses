import { config } from "@/lib/auth"
import nextAuth from "next-auth"

const handler = nextAuth(config)

export { handler as GET, handler as POST }
