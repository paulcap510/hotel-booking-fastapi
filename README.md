# Hotel Booking Platform

This is a hotel booking platform similar to Hotels.com or Agoda. Users can create accounts, search for hotels, and make booking on the site.

## Features
- User signup/login
- Browse/search hotels
- Book a room


## Tech Stack
- Backend: FastAPI
- Templates: Jinja2
- Database: SQLite (via SQLAlchemy ORM)
- Auth: Session-based (see below)

## Architecture Decisions

### Session-based Auth

This app is server-rendered (FastAPI + Jinja2), so the browser and server are always talking to each other directly — there's no separate frontend client or third-party API consuming this auth. JWTs are designed for stateless auth across systems that don't share a session store (e.g. a SPA talking to a separate API, or multiple services validating a token independently). Since that's not the architecture here, session cookies are simpler, easier to revoke, and avoid the storage/XSS pitfalls of handling JWTs in a browser context.

## Setup / Running locally

# clone repo
https://github.com/paulcap510/hotel-booking-fastapi
cd hotel-booking-fastapi

# install dependencies
pip install -r requirements.txt

# run the server
uvicorn app.main:app --reload

## Next Steps
- [ ] Add session cookies to handle login
