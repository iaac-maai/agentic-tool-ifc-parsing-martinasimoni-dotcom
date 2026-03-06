# IFCore Platform

Two deployments: FastAPI on HuggingFace Spaces + React/Worker on Cloudflare Pages.

**Actual flow (polling, not callbacks — HF Spaces cannot resolve *.workers.dev DNS):**

```
Browser → CF Worker POST /api/checks/run
            → reads IFC from R2, encodes as base64
            → POST {ifc_b64, project_id} to HF Space /check
            → HF returns {job_id} immediately, runs checks in background
Browser polls CF Worker GET /api/checks/jobs/:id every 2s
            → CF lazy-polls HF GET /jobs/{hf_job_id}
            → when done: remaps job_id, inserts to D1, returns results
```

Key decisions:
- **Base64 IFC in request body** — avoids HF having to download from CF URLs it can't resolve
- **Lazy polling** — CF only polls HF when the browser asks, no background tasks
- **job_id remapping** — HF generates its own UUIDs; must remap to CF job UUID before D1 insert

---

## Live Deployment (serJD)

| What | Where |
|------|-------|
| HF Space | `https://serjd-ifcore-platform.hf.space` |
| CF Worker | `https://ifcore-platform.tralala798.workers.dev` |
| D1 database | `bf5f1c75-8fea-4ec7-8033-c91a8e61b160` |

All provisioned and E2E tested Feb 19 2026. ✅

---

## Local Dev

Two terminals. Python 3.10+, Node 18+.

```bash
# Terminal 1
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 7860

# Terminal 2
cd frontend && npm install && npm run db:migrate
echo "HF_SPACE_URL=http://localhost:7860" > .dev.vars
npm run dev                        # → http://localhost:5173
```

`@cloudflare/vite-plugin` emulates D1/R2 locally. No cloud accounts needed.

---

## Deploy — Owner (serJD)

```bash
# Backend → HF (~2 min build)
pip install huggingface_hub && huggingface-cli login
bash backend/deploy.sh

# Frontend → Cloudflare
cd frontend
npm run deploy                     # always use this — runs vite build first
```

⚠️ Never use `npx wrangler deploy` directly — it skips the Vite build and deploys stale code.

---

## Deploy — New Owner (fork)

**Accounts needed:** GitHub · HuggingFace (free) · Cloudflare (free tier)

1. Fork `SerjoschDuering/ifcore-platform` on GitHub
2. Create HF Space: `hf.co/new-space` → SDK: Docker → name: `ifcore-platform`
3. Edit **2 files**:
   - `backend/deploy.sh` line 5: `HF_REPO="YOURHFNAME/ifcore-platform"`
   - `frontend/wrangler.jsonc`: `database_id` (from step 4) + `HF_SPACE_URL: "https://YOURHFNAME-ifcore-platform.hf.space"`
4. `wrangler d1 create ifcore-db` → paste ID into wrangler.jsonc
5. `wrangler r2 bucket create ifcore-files`
6. `bash backend/deploy.sh`
7. `cd frontend && npm run db:migrate:remote && npm run deploy`

> HF URL pattern: username lowercased. `MyName` → `myname-ifcore-platform.hf.space`

---

## Adding a Team Repo (captains)

**macOS / Linux / Git Bash:**
```bash
git submodule add -f https://github.com/ORG/team-repo backend/teams/team-name
git commit -m "add team-name submodule"
```

**Windows PowerShell** (no bash — run these instead of deploy.sh):
```powershell
# Add submodule
git submodule add -f https://github.com/ORG/team-repo backend/teams/team-name
git commit -m "add team-name submodule"
# Notify the instructor to run deploy.sh — Windows cannot push to HF Spaces directly
```

> The `-f` flag is required because `.gitignore` excludes `backend/teams/*/` by default (only `demo/` is exempt). The flag overrides this for submodules.

After adding, notify the instructor to run `bash backend/deploy.sh` to redeploy to HF Spaces.

Orchestrator auto-discovers all `check_*` functions in `teams/*/tools/checker_*.py`.

---

## Check Function Contract

> The orchestrator only picks up `checker_*.py` files and `check_*` functions. Everything else in the team repo is ignored — notebooks, helpers, `main.py` etc. are all fine to have.

### File naming
- File must be in `tools/` directory inside the team repo
- File name must match `checker_*.py` (e.g. `checker_walls.py`, `checker_doors.py`)
- ❌ `main.py`, `toola.py`, notebooks (`.ipynb`) are ignored entirely

### Function naming
- Function name must start with `check_` (e.g. `check_door_count`, `check_wall_fire_rating`)
- ❌ `toola()`, `toolb()`, `run()` are ignored

### Signature
```python
def check_something(model, **kwargs) -> list[dict]:
```
- First arg must be `model` (an `ifcopenshell.file` object)
- Return a **list of dicts**, one dict per element checked

### Required dict keys
Every dict in the returned list must have **all** of these keys:

| Key | Type | Notes |
|-----|------|-------|
| `element_id` | str or None | GlobalId of the IFC element |
| `element_type` | str | e.g. `"IfcDoor"`, `"IfcWall"`, `"Summary"` |
| `element_name` | str | Short display name |
| `element_name_long` | str or None | Full name if available |
| `check_status` | str | One of: `pass` `fail` `warning` `blocked` `log` |
| `actual_value` | str | What was found |
| `required_value` | str | What was expected |
| `comment` | str or None | Human-readable explanation |
| `log` | str or None | Debug info |

### Minimal working example
```python
def check_door_count(model, min_doors=2):
    doors = model.by_type("IfcDoor")
    results = []
    for door in doors:
        results.append({
            "element_id": door.GlobalId,
            "element_type": "IfcDoor",
            "element_name": door.Name or f"Door #{door.id()}",
            "element_name_long": None,
            "check_status": "pass",
            "actual_value": "Present",
            "required_value": f">= {min_doors} doors total",
            "comment": None,
            "log": None,
        })
    return results
```

Full example: `backend/teams/demo/tools/checker_demo.py`

---

## Known Gotchas

1. **HF cold start** — after 48h inactivity Space sleeps; first request takes 10–60s
2. **HF in-memory jobs** — `_jobs` dict resets on Space restart; pending jobs stuck "running" in D1, users must re-submit
3. **`*.workers.dev` DNS** — HF Spaces cannot resolve CF Worker URLs; never pass them as download targets to HF
4. **`npm run deploy` vs `npx wrangler deploy`** — always use the npm script
5. **Windows + `deploy.sh`** — `bash` is not available in plain PowerShell. Use Git Bash, WSL, or ask the instructor to run the deploy. The `git submodule add -f` step works in PowerShell directly.
6. **`git submodule add` blocked by .gitignore** — always use the `-f` flag: `git submodule add -f <url> backend/teams/<name>`. Without `-f` it fails with "already exists in the index" or is silently blocked.
7. **Other files in team repos are ignored by design** — orchestrator only picks up `checker_*.py` / `check_*`. Notebooks, `main.py`, helper modules etc. are untouched.

---

## Key Files

| File | What |
|------|------|
| `backend/main.py` | FastAPI: `/health`, `POST /check`, `GET /jobs/{id}` |
| `backend/orchestrator.py` | Discovers + runs `check_*` functions |
| `backend/deploy.sh` | **Change `HF_REPO`** for new owner · flatten submodules → push to HF |
| `frontend/wrangler.jsonc` | **Change `database_id` + `HF_SPACE_URL`** for new owner |
| `frontend/migrations/0001_init.sql` | D1 schema |
| `frontend/.dev.vars` | Local env overrides — gitignored, never commit |
