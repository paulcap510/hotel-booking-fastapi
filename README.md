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

### Booking Availability

Room availability isn't stored as a static value. It's calculated at request time as `total_inventory` minus confirmed bookings that overlap the requested date range. This avoids an entire class of bugs where a stored "available" flag drifts out of sync with reality (e.g. forgetting to restore it after a cancellation).

## Setup / Running locally

# clone repo
https://github.com/paulcap510/hotel-booking-fastapi
cd hotel-booking-fastapi

# install dependencies
pip install -r requirements.txt

# run the server
uvicorn app.main:app --reload

## Next Steps/Limitaitons
[ ] Sessions currently stored in memory, and they reset on server restart and won't work across multiple server instances. Should move to a database table or Redis before any real deployment.
[ ] Booking creation re-validates availability inside a transaction right before commit to reduce race conditions on concurrent bookings; full prevention would require row-level locking (e.g. via Postgres), which SQLite doesn't support.
[ ] [ ] A middleware checks login state on every request (to show correct navbar state, etc.), which queries the database each time. Fine at this scale; at higher traffic this should be backed by a cache (e.g. Redis) so most requests don't hit the database just to check who's logged in.
[ ] No CSRF token yet on form-based routes.
