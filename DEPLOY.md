# Deploying the Prasang Explorer to Render

This is a Flask app that loads the embedding index into memory and calls Gemini +
Groq at runtime. Render runs it with gunicorn (see `render.yaml`).

## 0. Rotate your API keys first
The Gemini, Groq keys (and the Netlify token / OAuth secret) were shared in chat —
treat them as compromised. Create fresh `GEMINI_API_KEY` and `GROQ_API_KEY` and use
the new values in step 3. Never commit `.env` (it is gitignored).

## 1. Put the code on GitHub
From this folder (a git repo is already initialised and committed):

```
gh auth login                      # one-time, if not already
gh repo create prasang-explorer --private --source . --push
```
or manually: create an empty GitHub repo, then
```
git remote add origin https://github.com/<you>/prasang-explorer.git
git push -u origin main
```

## 2. Create the Render service
- Go to https://dashboard.render.com → **New +** → **Blueprint**.
- Connect the GitHub repo. Render reads `render.yaml` and creates the web service.

## 3. Set the secrets
When prompted (or in the service's **Environment** tab), set:
- `GEMINI_API_KEY` = your rotated Gemini key
- `GROQ_API_KEY` = your rotated Groq key

(`PYTHON_VERSION` is already pinned in `render.yaml`.)

## 4. Deploy
Render builds (`pip install -r requirements.txt`) and starts
(`gunicorn app:app`). When it's live you get a public `https://prasang-explorer.onrender.com`
URL.

## Notes
- **Free tier sleeps** after ~15 min idle; the first request after that takes ~30–60s
  to wake (it reloads the embeddings). Subsequent requests are fast.
- Required data files are committed and ship with the repo: `recategorized_stories.json`,
  `embeddings.npy`, `topic_embeddings.npy`, `topics.json`, `glossary.json`,
  `embeddings_meta.json`, `stories_base.json`.
- To redeploy after changes: `git push` (Render auto-deploys), or click **Manual Deploy**.
