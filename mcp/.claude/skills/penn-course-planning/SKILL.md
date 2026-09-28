---
name: penn-course-planning
description: Plan University of Pennsylvania courses using the penn-course MCP server — search the catalog, read Penn Course Review ratings, compare courses, detect schedule time-conflicts, and assemble a weekly schedule. Use whenever the user asks about Penn/UPenn courses, professors, course difficulty/workload/quality, what classes to take, fulfilling a requirement or attribute (Gen-Ed), or building/checking a semester schedule.
---

# Penn course planning

This skill drives the **`penn-course`** MCP server (tools are named `search_courses`,
`get_course_details`, etc.). It talks to the public Penn Courses / Penn Course Review API,
so data is real and current. No auth is required for catalog data and aggregate ratings.

**Detailed reviews are enabled** on this setup: a logged-in Penn session cookie
(`PENN_COURSES_SESSION_COOKIE`) is configured, so `get_course_reviews` returns full
per-instructor written reviews — not just aggregates. Call `get_current_semester` to confirm
(`reviews_enabled: true`). The session cookie expires periodically (logout / Penn timeout);
when it lapses, `get_course_reviews` silently falls back to public aggregates and reports
`auth_status: unauthenticated` — that's the cue to refresh the cookie, not a bug.

## Conventions (read first)

- **Course codes**: `SUBJECT-NUMBER`, e.g. `CIS-1200`, `MATH-1400`, `ECON-0100`. Always
  hyphenated and uppercase. If the user writes "CIS 120" or "cis120", normalize to `CIS-1200`
  (Penn moved to 4-digit codes; `CIS-120` → `CIS-1200`, `CIS-160` → `CIS-1600`).
- **Section ids**: course code + 3-digit section, e.g. `CIS-1200-001`.
- **Semester**: term code like `2026C` (`A`=spring, `B`=summer, `C`=fall). Omit the
  `semester` argument to use the current term; call `get_current_semester` first if unsure.
- **Ratings scale**: roughly 0–4. Higher `course_quality` / `instructor_quality` is better;
  **lower** `difficulty` and `work_required` mean a lighter course. Some courses are unrated
  (`null`) — say so rather than treating null as 0.
- **Meeting times** come back already formatted as `HH:MM` ranges with day codes
  `M T W R F` (**R = Thursday**). Don't re-parse Penn's raw `HH.MM` encoding yourself.

## Tools at a glance

| Goal | Tool |
| --- | --- |
| Current term + auth status | `get_current_semester` |
| Find courses by keyword/code | `search_courses` |
| Full course info + sections | `get_course_details` |
| Just the sections/meeting times | `list_course_sections` (filters: `open_only`, `activity`) |
| Aggregate ratings | `get_course_ratings` |
| Detailed PCR reviews | `get_course_reviews` (falls back to aggregates if unauthenticated) |
| Courses with an attribute / Gen-Ed | `find_courses_by_attribute` |
| Courses fulfilling a requirement | `find_courses_by_requirement` |
| Do these sections clash? | `check_schedule_conflicts` |
| Build a weekly schedule | `build_schedule` |
| Rank by quality/difficulty/workload | `recommend_courses` (`sort_by=...`) |
| Side-by-side comparison | `compare_courses` |
| List your saved PCP schedules | `list_schedules` (requires auth) |
| **Save a schedule to penncourseplan.com** | `save_schedule` (requires auth — **writes to your account**) |
| Delete a saved schedule | `delete_schedule` (requires auth) |

## Workflows

**"Tell me about CIS 1200 / is it hard / who teaches it?"**
→ `get_course_details` (description, prereqs, attributes, sections) +
`get_course_ratings`. For per-instructor depth use `get_course_reviews` — with the configured
session cookie this returns full written breakdowns per instructor; if the cookie has expired
it returns aggregates plus an `unauthenticated` note (expected, not an error).

**"What's a good / easy class about <topic>?"**
→ `recommend_courses` with the topic as `query`. Use `sort_by="course_quality"` for "good",
`sort_by="difficulty"` or `"work_required"` for "easy/light". Present the top few with their
ratings, and flag unrated ones.

**"Compare CIS 1200 vs CIS 1600."**
→ `compare_courses` with both codes. Summarize the quality/difficulty/workload deltas and
note prereq differences.

**"Does this schedule work / do these classes conflict?"**
→ Resolve each course to a concrete **section id** first (use `list_course_sections` to pick
sections, ideally `open_only=true`). Then `check_schedule_conflicts` for a quick yes/no, or
`build_schedule` for the full weekly grid + total credits + missing-companion warnings
(e.g. a LEC that needs a REC/LAB). Report any `not_found` section ids back to the user.

**"What fulfills <requirement / Gen-Ed attribute>?"**
→ `find_courses_by_attribute` when you have an attribute code (use `match="description"` to
search by words; add `prefilter_query` to narrow a big catalog and keep it fast), or
`find_courses_by_requirement` for a requirement name/code.

**"Save / push this schedule to Penn Course Plan so I can see it on the site."**
→ `save_schedule(name, sections=[...])` writes a new schedule to the user's **live**
penncourseplan.com account; it appears after they refresh and pick it from the schedule
dropdown. This is a **real mutation on their account** — confirm the course list and the name
first, and default to creating a *new* schedule rather than overwriting one. Pass
`schedule_id` only to deliberately overwrite an existing schedule (find ids via
`list_schedules`). Use `delete_schedule` to remove one. All three need the session cookie
(`reviews_enabled: true` is a good proxy that auth is configured); without it they return a
clear `WriteAuthRequired` error, never a crash.

## Good habits

- Lead with `get_current_semester` when the term matters or the user didn't specify one.
- When a course or section isn't found, double-check the code format before telling the user
  it doesn't exist — most "not found" results are a `CIS 120` vs `CIS-1200` normalization miss.
- Quote real numbers from the tools (quality 2.8, difficulty 3.0…) and cite the section/day/time
  rather than paraphrasing vaguely. Distinguish "lightly rated / no reviews" from "low rating".
- The data is a snapshot of the live catalog; sections fill up, so treat `status`/capacity as
  point-in-time.
