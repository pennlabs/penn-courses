export enum Status {
	OPEN = "O",
	CLOSED = "C",
	CANCELLED = "X",
	UNLISTED = "",
}

export type WebhookPayload = {
	previous_status: Status,
	section_id: string;
	section_id_normalized: string;
	status: Status;
	term: string;
};
