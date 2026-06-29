# Hotel Booking Platform

This is a hotel booking platform similar to Hotels.com or Agoda. Users can create accounts, search for hotels, view and manage their bookings, and get help through a dedicated support page.

## Features

### Implemented
- User signup/login (session-based auth), logout
- Hotel search by city, dates, and guest count, with real-time availability checking
- Hotel and room browsing with detail pages
- Book a room, with availability and capacity validation
- Booking confirmation page
- My Trips: view bookings split into upcoming, current, past, and cancelled
- Booking detail page (read-only summary)
- Manage booking page: edit guest contact info, change dates/guests (with availability re-check), and cancel (with confirmation modal)
- Role-based authorization: admin-only booking deletion (is_admin flag; no admin UI yet)
- Navbar reflects real login state across the whole site
- Support/FAQ page with live search
-
### Planned / Not yet built
- [ ] User profile editing (name, email)
- [ ] Password reset
- [ ] Host/property-owner accounts
- [ ] Reviews and ratings (currently hardcoded placeholder data)

## Tech Stack
- Backend: FastAPI
- Templates: Jinja2
- Database: SQLite (via SQLAlchemy ORM), migrations via Alembic
- Auth: Session-based (see below)
- Frontend: Bootstrap 5, Flatpickr for date selection

## Architecture Decisions

### Session-based Auth
This app is server-rendered (FastAPI + Jinja2), so the browser and server are always talking to each other directly — there's no separate frontend client or third-party API consuming this auth. JWTs are designed for stateless auth across systems that don't share a session store (e.g. a SPA talking to a separate API, or multiple services validating a token independently). Since that's not the architecture here, session cookies are simpler, easier to revoke, and avoid the storage/XSS pitfalls of handling JWTs in a browser context.

A middleware checks the session cookie on every request and attaches the current user (or `None`) to `request.state.user`. This is what lets the navbar, and any other server-rendered page, reflect login state without each route needing its own login-check logic.

### Booking Availability
Room availability isn't stored as a static value. It's calculated at request time as `total_inventory` minus confirmed bookings that overlap the requested date range. This avoids an entire class of bugs where a stored "available" flag drifts out of sync with reality (e.g. forgetting to restore it after a cancellation).

### Shared booking logic
Booking creation is consolidated into a single function (`create_booking_for_user`) used by both the JSON API route and the HTML form route, so validation rules and the availability/transaction-safety logic only need to live in one place. The same pattern is used for fetching a user's bookings (`get_bookings_for_user`), shared between the JSON API and the Jinja-rendered My Trips page.

## Setup / Running locally
\`\`\`bash
git clone https://github.com/paulcap510/hotel-booking-fastapi.git
cd hotel-booking-fastapi

pip install -r requirements.txt

uvicorn main:app --reload
\`\`\`

## Next Steps / Limitations
- [ ] Sessions are currently stored in memory; they reset on server restart and won't work across multiple server instances. Should move to a database table or Redis before any real deployment.
- [ ] Booking creation re-validates availability right before commit to reduce race conditions on concurrent bookings; full prevention would require row-level locking (e.g. via Postgres), which SQLite doesn't support.
- [ ] The login-state middleware queries the database on every request. Fine at this scale; at higher traffic this should be backed by a cache (e.g. Redis) so most requests don't hit the database just to check who's logged in.
- [ ] No CSRF token yet on form-based routes; `SameSite=Lax` mitigates the most common attack vectors but a dedicated token would be a stronger production-grade defense.
- [ ] Hotel images are a single field for now; a real implementation would support multiple images per hotel (gallery, primary image for search results).
- [ ] No rate limiting on login.
- [ ] Search currently has limited demo data (a handful of hotels); search/filter logic is implemented and tested, but not yet backed by a large realistic dataset.
- [ ] Host/property-owner accounts not yet implemented — currently all users are guests; a real marketplace would let hosts list and manage their own properties.