# HCST Smart Campus Guide

A Streamlit web app for campus navigation, department discovery, faculty directory,
appointment requests, visitor help journeys, a campus Q&A assistant, events and lost & found
for Hindustan College of Science and Technology, Farah, Mathura.

All faculty names, contacts and timings are **synthetic demo data**.
Campus marker positions are **approximate** until verified (see Admin page).

## Deploy (no local install)
1. Create a GitHub repo and upload `app.py`, `requirements.txt`, `README.md`, `.gitignore`.
2. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**.
3. Pick the repo, branch `main`, main file `app.py`, then **Deploy**.
4. (Optional) In app **Settings → Secrets** add: `ADMIN_PASSWORD = "your-strong-password"`.

Default admin password if no secret is set: `admin123` (change it!).

## Accounts & theme
- Visitors can browse everything without an account. Booking a meeting and Lost & Found reports need a (free) user account.
  Set `REQUIRE_LOGIN_FOR_ACTIONS = False` in `app.py` to turn this off.
- Passwords are stored salted + hashed (PBKDF2). Admins can reset/delete users in **Admin → Users**.
- Accounts live in the app's SQLite file, which resets when Streamlit Cloud restarts the app.
- Theme: `.streamlit/config.toml` (colours) + CSS at the top of `app.py`.
