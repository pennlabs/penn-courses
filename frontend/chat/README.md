# Penn Course Chat

A standalone chat assistant for exploring Penn's course catalog. It talks to
`POST /api/chat/`, served by the `chat` Django app, which runs the tool-use loop and can
search courses, pull up a single course with its sections, and read Penn Course
Review data.

This is deliberately a separate app rather than a tab inside Penn Course Plan, so
the assistant can be iterated on and released independently. It reads and writes the
same cart and schedules as Penn Course Plan, scoped to the logged-in student.

Tool calls are shown as a trace above each reply, with a line running down into the
answer. Each step carries an icon for its tool, and steps that changed the student's
plan get a filled node so an edit never looks like a lookup.

While a turn is in flight the line ends on a pulsing node rather than elbowing into a
reply — there is no reply yet, and an empty bubble is just a blank box. The bubble
appears with the first fragment of text, trailing a blinking caret until the turn
finishes.

## Running it

The backend has to be running on port 8000, with an Anthropic API key in its
environment (see `backend/README.md` — note that nothing loads `.env`
automatically):

```bash
cd backend
uv run --env-file .env manage.py runserver
```

Then, from `frontend/`:

```bash
yarn install
yarn workspace penncoursechat dev
```

The app comes up on <http://localhost:3001> and proxies `/api` and `/accounts` to
the backend, so the session cookie that authenticates the chat route works normally.
You will be asked to log in with PennKey on first load.

The proxy is `server.js` (express + `http-proxy-middleware`), the same shape Penn
Course Plan uses, rather than Next's built-in `rewrites` — it pipes streamed responses
through untouched and lets us set our own timeout.

Port 3001 keeps it clear of Penn Course Plan on 3000, so both can run at once.

If you change the port, add the new one to `CSRF_TRUSTED_ORIGINS` in
`backend/PennCourses/settings/development.py`. Django checks the browser's `Origin`
header against that list on every POST, so an unlisted port makes every message
fail with a 403 — even when you are logged in.

## Layout

| Path | What it is |
| --- | --- |
| `pages/index.tsx` | Auth gate — shows the login screen or the chat |
| `components/Chat.tsx` | The full-page chat: transcript, empty state, composer |
| `components/Message.tsx` | One turn, plus the trace of what the assistant looked up |
| `components/icons.tsx` | The per-tool icons that sit on the trace line |
| `components/Markdown.tsx` | Renders a reply's Markdown and linkifies course codes |
| `components/CourseChip.tsx` | A course code: links to PCR, positions the blurb |
| `components/CourseBlurb.tsx` | The blurb itself |

| `lib/api.ts` | Backend calls and their types |
| `lib/useChat.ts` | Conversation state |
| `server.js` | Dev server: proxies `/api` and `/accounts` to Django |

## Course previews

Replies are Markdown, rendered with `react-markdown`. Raw HTML in a reply is escaped
rather than rendered and `javascript:` URLs are stripped, so nothing the model writes
can inject markup.

GFM pipe tables are supported, and the system prompt tells the assistant when they are
worth using — comparing several courses on the same few attributes — and when bullets
read better. Numeric columns are right-aligned with `---:`, which arrives as an inline
`text-align` style on each cell; the renderer forwards it and sets `tabular-nums` so
the digits line up. A table wider than the message bubble scrolls inside it rather than
stretching the transcript. Course codes inside cells become links like anywhere else.

Every course code in a reply becomes a link to that course on Penn Course Review, and
on hover or keyboard focus it shows a blurb — the course code and title, a "view in
PCR" link, and the four colored scoreboxes for course quality, instructor quality,
difficulty, and work.

`CourseBlurb.tsx` builds that on this app's data and styled-components rather than
importing Degree Plan's `Infobox`. Sharing the component was tried and reverted: it is
wired to Emotion, `react-tooltip`, `react-string-replace` and a `next/font` module, and
it hides the whole scorebox when a course has no reviews — which left a near-empty card
for the many courses that have none. The scorebox colors and thresholds are still
copied from `degree-plan/components/Infobox/InfoRatings.js`, including the reversed
scales where a low difficulty or workload is the green one, so a rating reads the same
in both products.

Two deliberate differences. A course with no reviews says so instead of rendering a
blank card, and a missing rating is grey rather than green, since green reads as "good"
for a course nobody has rated. There is also no "view in PCR" button — this is a hover
card, and the course code that opens it is already the link.

The blurb data rides along in the chat response's `courses` field: the backend collects
it from the lookups the assistant performed, narrows it to the codes the reply mentions,
and fills any gaps from the catalog in a single query. That last step matters — which
fields a lookup carries depends on which tool surfaced the course, and the schedule and
degree-plan tools report what is in the plan rather than what the catalog knows. Without
it, a course the assistant only saw in the student's cart got a blurb saying it had no
Penn Course Review data, when nobody had looked it up. A blurb still costs no extra
request and can never contradict the answer next to it.

The pattern that recognizes a course code lives in two places that must agree —
`COURSE_CODE` in `components/Markdown.tsx` and `COURSE_CODE_RE` in
`backend/chat/agent.py`. If a code is not matched by both, it renders as plain text
with no link. A code the model mentions without having looked it up still links to
PCR; it just has no blurb.

## Streaming

The app talks to `POST /api/chat/stream/`, which answers Server-Sent Events rather
than one JSON body. Frames are `text` (a fragment of the reply), `tool_call` (a lookup
that just ran), `done` (the assembled turn), and `error`.

This is not only nicer to watch. A turn takes as long as it takes — the backend makes
a model round trip per batch of tool calls — and a single long request will eventually
meet a proxy that gives up on it. Next's own rewrite proxy did exactly that at 30
seconds, returning a 500 while Django kept working, so a schedule change would land
with no reply to show for it. Bytes on the wire keep the connection alive; in practice
the first fragment arrives a second or two in.

Errors can surface two ways, and the client turns both into the same thing. Before the
response starts, as an HTTP status. After it has started — when there is no status left
to set — as an `error` frame.

Partial output is discarded when a turn fails. Half an answer that stops mid-sentence
still reads as fact, and the student has no way to tell how much is missing.

`POST /api/chat/` still returns the whole turn as JSON. It is the documented API and
what the tests drive; the streaming route is a second view over the same agent.

## Conversation state

The backend keeps no conversation state, so `useChat` resends the whole history with
every message. It holds confirmed turns separately from the in-flight and failed ones,
which keeps that history strictly alternating even when a request fails — the API
rejects anything else.
