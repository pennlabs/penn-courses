# Prerequisite Scraping Commands

Run all commands from `backend/`.

## Common command

```bash
uv run manage.py scrape_prereqs --all-course-codes --semesters 2026C --max-requests 100 --sleep-seconds 0.1 --jitter-seconds 0.1
```

What it does:
- `--all-course-codes`: loads one course/CRN pair per course code from the DB.
- `--semesters 2026C`: limits the DB query to semester `2026C`.
- `--max-requests 100`: caps total requests after deduplication.
- `--sleep-seconds 0.1`: fixed delay between requests.
- `--jitter-seconds 0.1`: adds random delay in `[0, 0.1]` seconds per request.

## Other useful forms

```bash
uv run manage.py scrape_prereqs --pair "CIS 1210:14309"
uv run manage.py scrape_prereqs --input-file courses/data/prereq_scrapes/targets.sample.json
uv run manage.py scrape_prereqs --all-course-codes --semesters all
```

## Output location

By default, output JSON files are written in this directory:

- `courses/data/prereq_scrapes/`

## Populate structured prereqs into DB

After scraping, use the `populate_prereqs` command to parse the JSON files and write structured prereq links into the DB.

```bash
# Dry-run first (no DB writes)
uv run manage.py populate_prereqs --semesters 2026C --dry-run

# Apply writes
uv run manage.py populate_prereqs --semesters 2026C
```
Use `--scrape-file <path>` to target a specific scrape JSON.
Use `--clear-existing` only if you want to replace existing prereq links for matched courses.

## Notes

- If a semester value fails (for example typo or unavailable code), run with a known semester code, or use `--semesters all`.
- To see all command options:

```bash
uv run manage.py scrape_prereqs --help
```
