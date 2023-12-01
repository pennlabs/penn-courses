export type Nullable<T> = T | null
export type Optional<T> = T | undefined

export type NonNullable<T> = T extends null | undefined ? never : T
