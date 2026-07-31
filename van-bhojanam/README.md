# Van Bhojanam 🌿

Forest-themed jungle-dining reservation site. Diners browse a seasonal menu,
pick a "forest zone" table (each with its own cover charge), pay a small
eco levy, and check out via UPI/Card. A tiny live dashboard shows total
revenue and bookings made, pulled from the backend.

```
van-bhojanam/
├── frontend/
│   └── index.html       # static site — menu, zone picker, cart, checkout, dashboard
├── backend/
│   ├── main.py           # FastAPI app — /api/checkout, /api/stats
│   └── requirements.txt
└── render.yaml            # Render Blueprint — deploys both services
```

## Run it locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to see the API.

**Frontend**
```bash
cd frontend
python -m http.server 5500
```
Visit `http://localhost:5500`. The frontend is already pointed at
`http://localhost:8000` via `API_BASE_URL` at the top of the `<script>`
block in `index.html` — no build step needed.

## Deploy to Render

This repo includes a `render.yaml` Blueprint that provisions **two services**:

| Service | Type | Root | What it does |
|---|---|---|---|
| `van-bhojanam-api` | Python web service | `backend/` | FastAPI booking API |
| `van-bhojanam-web` | Static site | `frontend/` | The booking site itself |

**Steps:**
1. Push this repo to GitHub (see below).
2. In the Render dashboard: **New → Blueprint**, connect the `van-bhojanam` repo. Render will read `render.yaml` and create both services.
3. Once `van-bhojanam-api` deploys, copy its URL (e.g. `https://van-bhojanam-api.onrender.com`).
4. Open `frontend/index.html`, update the `API_BASE_URL` constant near the top of the `<script>` block to that URL.
5. Commit and push — the static site redeploys automatically and now talks to the live API.
6. (Optional, recommended) In the Render dashboard, set the `van-bhojanam-api` service's `FRONTEND_ORIGINS` env var to your static site's exact URL instead of `*`, to lock down CORS.

Render's free-tier web services spin down after inactivity, and the API's
in-memory booking/revenue counters reset on every restart — that's expected
for this demo setup. Swap the in-memory `Store` in `main.py` for a real
database (e.g. Render Postgres) if you need bookings to persist.

## Push to GitHub

From inside `van-bhojanam/` (already git-initialized with an initial commit):

**Option A — using the `gh` CLI** (if you have it installed and are logged in):
```bash
gh repo create van-bhojanam --public --source=. --remote=origin --push
```

**Option B — manual:**
1. Create a new empty repo at https://github.com/new named `van-bhojanam` (don't initialize it with a README/license — this repo already has one).
2. Then run:
```bash
git remote add origin https://github.com/<your-username>/van-bhojanam.git
git branch -M main
git push -u origin main
```
