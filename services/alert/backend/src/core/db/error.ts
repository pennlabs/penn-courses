export const isDuplicateKeyError = (error: unknown) => {
	return (error as { code: string })?.code === '23505'
}
