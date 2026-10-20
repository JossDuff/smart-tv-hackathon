# Vision requests (omp session → claude code session)

omp (the other assistant) cannot see images — this file is how you relay vision for it.

**Workflow, repeated whenever omp says a new request is pending:**
1. omp takes a camera snapshot of the TV and appends a request below.
2. You run, from the repo root in your claude code session:
   `claude "Read shared/vision/REQUEST.md, look at the image(s) the latest pending request references, answer its questions concisely, and write the answer to shared/vision/RESPONSE.md"`
3. Tell omp "vision done" in its chat (or it will check RESPONSE.md itself on its next step).

---

## Request 55 (PENDING, HIGHEST PRIORITY) — 2026-10-19
- Image: `snaps/after_clicks.jpg` — after user manually pressed `select` several times while cursor was on/near a PoC button ("pwn it"/`Do It`/`Run It`)
- Context: network saw ONE new TLS flow to 3.19.84.251:443 (AWS us-east-2) right after the presses — a PoC click fired something. Need screen truth.
- Question: What is on screen NOW? Specifically: (1) any dialog or alert visible (text verbatim)? (2) did a new app/icon appear anywhere? (3) is the blog page still up, or did something change (exit browser, new page)? (4) where is the cursor and what has focus?
