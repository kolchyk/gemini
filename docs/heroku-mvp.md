# Heroku MVP Notes

This MVP uses in-memory background jobs instead of Redis.

Constraints:
- run the web app as a single process, otherwise job polling can hit a different worker and lose state;
- jobs and results disappear after dyno restart, deploy, or crash;
- this setup is meant for low traffic and one dyno only;
- long-running work must go through `POST /api/generate/submit` plus `GET /api/generate/status/{job_id}` polling.

Heroku requirement:
- keep the web process on one worker via `Procfile` using `uvicorn ... --workers 1`.
