# penn-course-mcp

An [MCP](https://modelcontextprotocol.io) server for University of Pennsylvania course
planning. It is built on the public [Penn Courses](https://github.com/pennlabs/penn-courses)
API (the same backend behind Penn Course Plan and Penn Course Review), so the catalog,
ratings, and schedule data are live.

With it, an MCP client (Claude Desktop, Claude Code, or any other) can search the course
catalog, inspect sections and meeting times, read ratings and reviews, check a set of
sections for time conflicts, assemble a weekly schedule, and save that schedule back to a
Penn Course Plan account.

The server works with no configuration against the public API. Setting a session cookie
additionally unlocks detailed Penn Course Review breakdowns and the schedule-write tools. It
runs over stdio for local clients, or streamable HTTP when hosted.

> This package lives in the Penn Courses monorepo under `mcp/`. It talks to the Penn Courses
> API over HTTP and does not import the Django backend, so it can be developed and run on its
> own. All commands below are run from the `mcp/` directory.

## Tools

| Tool | What it does |
| --- | --- |
| `get_current_semester` | Active term code (e.g. `2026C`) and review-auth status |
| `search_courses` | Search the catalog by code or keyword; returns summaries and ratings |
| `get_course_details` | Full course info: description, prereqs, attributes, sections, meeting times |
| `list_course_sections` | Sections with formatted meeting times and instructors; filter by status or activity |
| `get_course_ratings` | Public aggregate ratings (quality, difficulty, workload) |
| `get_course_reviews` | Detailed PCR reviews when authenticated; falls back to aggregates otherwise |
| `find_courses_by_attribute` | Courses carrying a given attribute or Gen-Ed code |
| `find_courses_by_requirement` | Courses fulfilling a requirement (by code or name) |
| `check_schedule_conflicts` | Detect time conflicts among a set of section ids |
| `build_schedule` | Weekly grid, total credits, conflicts, and missing-companion warnings |
| `compare_courses` | Side-by-side ratings, difficulty, workload, and prereqs |
| `recommend_courses` | Search and rank by quality, difficulty, or workload |
| `list_schedules` | List the saved schedules in your Penn Course Plan account (auth) |
| `save_schedule` | Write a schedule to your Penn Course Plan account so it shows on the site (auth) |
| `delete_schedule` | Delete a saved Penn Course Plan schedule by id (auth) |

Course codes look like `CIS-1200`; section ids look like `CIS-1200-001`.

## Installation

```bash
cd mcp
uv pip install -e ".[dev]"   # or: pip install -e ".[dev]"
```

## Running

```bash
# stdio (default), for Claude Desktop / Claude Code
penn-course-mcp

# streamable HTTP at http://127.0.0.1:8000/mcp
penn-course-mcp --transport http --port 8000

# development server / MCP Inspector
fastmcp dev src/penn_course_mcp/server.py
```

### Client configuration

Add the server to your MCP client config (for Claude Desktop, this is
`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "penn-course": {
      "command": "uvx",
      "args": ["penn-course-mcp"],
      "env": {
        "PENN_COURSES_SESSION_COOKIE": ""
      }
    }
  }
}
```

> Use `"command": "penn-course-mcp"` instead of `uvx` if you installed the package into a
> virtualenv that is on your `PATH`.

## Configuration

All environment variables are optional (see [`.env.example`](.env.example)):

| Variable | Default | Purpose |
| --- | --- | --- |
| `PENN_COURSES_BASE_URL` | `https://penncoursereview.com` | API base URL |
| `PENN_COURSES_SEMESTER` | `current` | Default semester (`current` auto-resolves) |
| `PENN_COURSES_CACHE_TTL` | `3600` | Cache TTL (seconds) for catalog and detail data |
| `PENN_COURSES_TIMEOUT` | `20.0` | HTTP timeout (seconds) |
| `PENN_COURSES_USER_AGENT` | `penn-course-mcp/<ver>` | Sent with every request |
| `PENN_COURSES_SESSION_COOKIE` | _(unset)_ | Enables detailed reviews and schedule writes (see below) |
| `PENN_COURSES_TRANSPORT` / `--transport` | `stdio` | `stdio` or `http` |
| `PENN_COURSES_HOST` / `--host` | `127.0.0.1` | HTTP host |
| `PENN_COURSES_PORT` / `--port` | `8000` | HTTP port |

### Detailed reviews and schedule writes

The public API exposes aggregate ratings (course and instructor quality, difficulty, and work
required) without authentication. The detailed per-instructor Penn Course Review breakdowns,
and the schedule-write tools, require a logged-in Penn session. To enable them, log in to
penncoursereview.com, copy your session cookie, and set:

```bash
export PENN_COURSES_SESSION_COOKIE="sessionid=...; csrftoken=..."
```

`get_course_reviews` falls back to the public aggregate ratings when no cookie is set, so it
never errors. The schedule-write tools (`list_schedules`, `save_schedule`, `delete_schedule`)
read and modify a real Penn Course Plan account, so they always need the cookie. Writes also
need the `csrftoken` value, since Django enforces CSRF on unsafe methods. `save_schedule`
creates a new schedule by default; pass an existing `schedule_id` (from `list_schedules`) to
overwrite one instead.

> The read-only catalog and rating tools never modify your account. Only the three schedule
> tools do.

## Claude skill

This repository ships an optional [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)
at [`.claude/skills/penn-course-planning`](.claude/skills/penn-course-planning/SKILL.md). It
gives Claude guidance on using the tools well, including normalizing course codes (`CIS 120`
to `CIS-1200`), reading the rating scales, and choosing the right tool for schedule and
requirement questions. It activates automatically when you use Claude Code in this repository.
To make it available everywhere, copy it into your user skills folder:

```bash
cp -R .claude/skills/penn-course-planning ~/.claude/skills/
```

## Development

```bash
uv pip install -e ".[dev]"
pytest      # pure planning logic, mocked client, and tool tests
flake8      # style, import order (isort), and quote checks
black .     # formatter
```

The planning logic in `src/penn_course_mcp/planning.py` is pure and network-free, so the
schedule-conflict detection, time formatting, and comparison are covered by unit tests
without hitting the API.

## Notes

- Meeting times use Penn's `HH.MM` encoding (`10.15` is 10:15, `15.3` is 15:30). The server
  renders them as readable `HH:MM` ranges.
- Day codes are `M`, `T`, `W`, `R`, `F`, where `R` is Thursday.
- Back-to-back meetings, where one ends exactly as the next begins, are not counted as
  conflicts.
- This is an unofficial tool that consumes the public Penn Courses API. It caches responses
  and caps concurrency; please use it respectfully.

## License

MIT
