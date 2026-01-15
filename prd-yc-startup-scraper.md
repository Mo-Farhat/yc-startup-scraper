\# YC Startup Scraper — Product Requirements Document (PRD)

\## Objective

Build a Python scraper that collects structured data for ~500 Y Combinator startups.

The output dataset should include company info and founder LinkedIn details.

\### Primary Deliverables

\- CSV file with company details

\- Python script or Jupyter notebook

\- Small README with approach summary

\---

\## Functional Requirements

\### 1. Company Discovery

\- Fetch a list of YC companies using public API endpoints:

\- \`https://yc-oss.github.io/api/companies/all.json\`

\- Optional filtered endpoints (top companies, women/black-founded clusters)

\- OR use GraphQL: \`https://yc-graphql.vercel.app/\`

\- Ensure at least 500 unique companies are collected.

\### 2. Company Metadata Fields

For each company, collect:

\- \`company\_name\`

\- \`batch\`

\- \`short\_description\`

\- \`slug\` (for later detail scraping)

\- \`website\` (optional but useful)

\### 3. Founder Enrichment

For each company’s detail page (HTML):

\- Parse founder names

\- Parse LinkedIn URLs if present

\- If LinkedIn not present:

\- Optionally use a search API for enrichment

\- Document any fallback strategy

Columns in output:

\- \`founder\_name\`

\- \`founder\_linkedin\_url\`

Note: One row per founder is acceptable.

\### 4. Output Format

Export collected data to:

\- CSV file with columns:

company\_name, batch, short\_description, founder\_name, founder\_linkedin\_url

\---

\## Non-Functional Requirements

\### Performance

\- Script should complete within reasonable time (<10 min for 500 items)

\- Implement async/concurrency if feasible (optional)

\### Code Quality

\- Modular functions

\- Inline comments

\- Clear README explaining approach

\- Handle missing data gracefully

\---

\## Data Flow Overview

API LIST -> JSON -> Parse Basic Fields -> DETAIL HTML SCRAPE -> Parse Founders -> EXPORT CSV

\---

\## Stack & Tooling

\### Required

\- Python 3.10+

\- \`requests\`

\- \`pandas\`

\- \`beautifulsoup4\`

\### Optional / Bonus

\- \`aiohttp\` / \`asyncio\` for faster scraping

\- \`tqdm\` for progress bars

\---

\## Approach Summary (for README)

1\. Use YC public JSON/GraphQL API for listing companies.

2\. Save first ~500 companies.

3\. For each slug, fetch detail page HTML.

4\. Extract founder names and LinkedIn URLs.

5\. Export to CSV.

\---

\## Constraints & Assumptions

\- Founder LinkedIn info might not exist for every company.

\- HTML selectors may change — implement resilient parsing.

\- Respect YC site Terms of Service.

\---

\## Success Metrics

| Metric | Target |

|--------|--------|

| Dataset size | ≥ 500 unique startups |

| Founders extracted | ≥ 80% coverage |

| LinkedIn enrichments | ≥ 50% of founders |

| Script readability | Clear modular functions |