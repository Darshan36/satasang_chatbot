# Making the repo public (data in private Backblaze B2 bucket)

The app loads its data from a private **S3-compatible bucket** at startup, so the data
need not live in the repo — which lets the repo be public. When the `S3_*` env vars are
unset the app falls back to local files (local dev), so nothing breaks before the switch.

## Status
- ✅ Private B2 bucket **`chatbotsatsang`** created; the 6 data files uploaded
  (`recategorized_stories.json`, `embeddings.npy`, `topic_embeddings.npy`,
  `embeddings_meta.json`, `topics.json`, `glossary.json`). Re-run `python upload_data.py`
  after rebuilding data.
- App reads from S3 via `boto3` when `S3_BUCKET` is set.

## Render environment variables (the switch)
Set these on the Render service (Environment tab). Keep `GEMINI_API_KEY` / `GROQ_API_KEY`.
```
S3_BUCKET=chatbotsatsang
S3_ENDPOINT_URL=https://s3.eu-central-003.backblazeb2.com
S3_REGION=eu-central-003
S3_ACCESS_KEY_ID=<your B2 keyID>
S3_SECRET_ACCESS_KEY=<your B2 applicationKey>
```
After saving, Render redeploys; the log should read
`Loaded 491 stories, embeddings (491, 768), 45 topics (from s3://chatbotsatsang).`

## Make a clean, code-only PUBLIC repo
The current repo's **history contains the chat export**, so don't just flip it — start clean.
Stop tracking the data/export, gitignore them, then push a fresh history to a NEW public repo:

```
cd "C:\Users\Darshan\Downloads\Telegram Desktop\ChatExport_2026-05-01 (1)"
```
Add to `.gitignore`:
```
recategorized_stories.json
embeddings.npy
topic_embeddings.npy
embeddings_meta.json
stories_base.json
granular_stories.json
full_prasangs.json
individual_prasangs.json
categorized_*.json
summaries.json
messages.html
report.md
detailed_report.md
photos/
images/
css/
js/
```
Then (PowerShell):
```
Remove-Item -Recurse -Force .git
git init -b main
git add -A
git commit -m "Prasang Explorer (code only; data served from private B2 bucket)"
# create a NEW public repo on github.com, then:
git remote add origin https://github.com/Darshan36/prasang-explorer.git
git push -u origin main
```
Finally, in Render → **Settings → Build & Deploy → Repository**, point the service at the new
public repo. The keep-alive workflow comes with it and runs on unlimited public Actions minutes.
Keep `topics.json` / `glossary.json` in the repo if you like (they're non-sensitive); the app
still prefers the bucket copies when `S3_BUCKET` is set.

## Security
- The B2 key is bucket-scoped to `chatbotsatsang` — still keep it only in Render env vars and
  rotate it if it was shared anywhere.
- `embeddings.npy` is derived from the content; keeping it private (in the bucket) is the safe choice.
