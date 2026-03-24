# Deploy to Render

This app is ready for Render.

## Important
If you use Render free web service with SQLite, your database will reset when the instance is restarted or redeployed. To keep data permanently on Render, either:
- attach a persistent disk on a paid web service and set `DATABASE_PATH` to the mounted disk path, or
- move to Postgres later.

## Quick deploy
1. Push this folder to GitHub
2. Create a new Web Service on Render from that GitHub repo
3. Render should detect `render.yaml` automatically, or use:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Add environment variables:
   - `ADMIN_PASSWORD`
   - `SECRET_KEY`
5. Open the shell and run:
   - `flask --app app.py seed`

## Persistent SQLite on Render
Set `DATABASE_PATH` to something like:
`/var/data/orders.db`

That only works properly when a persistent disk is attached.
