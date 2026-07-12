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

### Host / Property Management
- Users can become a host (`is_host`) and access a host dashboard
- Hosts can list, edit, deactivate, and reactivate properties
- Hosts can add, edit, and delete rooms for their properties
- Hosts can view and manage bookings for their properties

### Experiences
- Hosts can create, edit, deactivate, and reactivate experience listings (e.g. tours, activities), including image upload
- Guests can browse experiences (homepage features a random rotating selection) and view experience detail pages
- Guests can submit a request to book an experience (date, guest count, optional message); total price is calculated and stored at request time
- Hosts can view incoming requests for their experiences and confirm or decline them
- Guests can track the status of their requests (pending/confirmed/declined) on a dedicated "My Experiences" page

### Experience Booking: Request-based, not instant-book
Unlike hotel room bookings (which are instant, capacity-checked reservations), experiences use a request-based flow: a guest submits a request, and the host must confirm or decline it. This mirrors how many real-world tour/activity platforms and bespoke service providers operate (as opposed to fixed-inventory, slot-based systems like Airbnb Experiences). This was a deliberate scope choice. A full slot/capacity-based scheduling system was considered but decided against for this project's scope in favor of the simpler request/response model.

### Planned / Not yet built
- [ ] Password reset emails are mocked — reset links are printed to the server console rather than sent via a real email provider. Production would integrate a transactional email service (e.g. SendGrid, SES).
- [ ] Reviews and ratings (currently hardcoded placeholder data)

## Tech Stack
- Backend: FastAPI
- Templates: Jinja2
- Database: PostgreSQL (via SQLAlchemy ORM), migrations via Alembic
- Auth: Session-based (see below)
- Frontend: Bootstrap 5, Flatpickr for date selection

## Architecture Decisions

### Session-based Auth
Since this app is fully server-rendered (FastAPI + Jinja2) with no separate frontend or third-party API involved, session cookies were chosen over JWTs, which simpler to revoke, and avoids the storage/XSS considerations of handling tokens in the browser. JWTs are better suited to stateless auth across systems that don't share a session store (e.g. a SPA calling a separate API), which isn't the case here.

A middleware checks the session cookie on every request and attaches the current user (or `None`) to `request.state.user`. This is what lets the navbar, and any other server-rendered page, reflect login state without each route needing its own login-check logic.

### Booking Availability
Room availability isn't stored as a static value. It's calculated at request time as `total_inventory` minus confirmed bookings that overlap the requested date range. This avoids an entire class of bugs where a stored "available" flag drifts out of sync with reality (e.g. forgetting to restore it after a cancellation).

### Shared booking logic
Booking creation is consolidated into a single function (`create_booking_for_user`) used by both the JSON API route and the HTML form route, so validation rules and the availability/transaction-safety logic only need to live in one place. The same pattern is used for fetching a user's bookings (`get_bookings_for_user`), shared between the JSON API and the Jinja-rendered My Trips page.

### Database: SQLite → PostgreSQL migration
This project started on SQLite for fast local iteration (zero setup, no separate server process). Once the app reached a stable feature set, it was migrated to PostgreSQL to move toward a more production-realistic setup — real concurrent write support, proper role-based permissions, and no reliance on SQLite's workarounds for schema changes (e.g. Alembic's `batch_alter_table`, needed because SQLite can't alter constraints on existing tables directly; Postgres supports this natively).

The migration had two parts:
- **Schema**: replayed via the existing Alembic migration history. One early migration (the initial "baseline") turned out to be a no-op — it had been generated against a SQLite database that already had tables created outside of Alembic's awareness, so it recorded no actual changes. This surfaced for the first time against a genuinely empty Postgres database. Resolved by building the schema directly from current models (`Base.metadata.create_all()`) and using `alembic stamp head` to bring Alembic's version tracking in sync with that state.
-
- **Data**: existing SQLite data (users, hotels, rooms, bookings, experiences, experience requests) was migrated with a custom script (`migrate_data.py`) that reads directly from SQLite and writes into Postgres via the existing SQLAlchemy models, preserving original primary keys (via `session.merge()`) so foreign key relationships stayed intact. Table order respects foreign key dependencies (parents before children). Password hashes transferred as opaque strings with no special handling needed, since hashing is one-way and login only ever re-hashes and compares — never decodes.

One pre-existing data integrity issue surfaced during migration: a handful of `rooms` rows referenced a `hotel_id` that no longer existed in `hotels` (orphaned from earlier local testing). SQLite hadn't enforced this relationship at insert time; Postgres correctly rejected it. Resolved by deleting the orphaned rows before completing the migration.

### Configuration
Database connection details are stored in a `.env` file (not committed to version control) and loaded via `pydantic-settings`. See `.env.example` for the required variables.

```bash
git clone https://github.com/paulcap510/hotel-booking-fastapi.git
cd hotel-booking-fastapi

pip install -r requirements.txt
```

Create a PostgreSQL database and role, e.g.:

```bash
psql postgres
```
```sql
CREATE DATABASE hotels_db;
CREATE USER your_app_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hotels_db TO your_app_user;
```

On Postgres 15+, also grant schema-level permissions (database-level privileges alone aren't sufficient to create tables):
```bash
psql -d hotels_db
```
```sql
GRANT ALL ON SCHEMA public TO your_app_user;
```

Create a `.env` file in the project root (see `.env.example`) with your connection string:
```
DATABASE_URL=postgresql://your_app_user:your_password@localhost:5432/hotels_db
```

Then run:
```bash
alembic upgrade head
uvicorn main:app --reload
```

This creates all tables via Alembic migrations against your PostgreSQL database. No sample data is included — sign up for an account, then use "Become a host" to create test hotels and experiences.


## Next Steps / Limitations
- [ ] Sessions are currently stored in memory; they reset on server restart and won't work across multiple server instances. Should move to a database table or Redis before any real deployment.
- [ ] Expired session and password-reset tokens aren't proactively cleaned up: they're only removed when someone attempts to use them. A production system would run a periodic background job to purge expired entries regardless of use.
- [ ] Booking creation re-validates availability right before commit to reduce race conditions on concurrent bookings; full prevention would require row-level locking (e.g. via Postgres), which SQLite doesn't support.
- [ ] The login-state middleware queries the database on every request. Fine at this scale; at higher traffic this should be backed by a cache (e.g. Redis) so most requests don't hit the database just to check who's logged in.
- [ ] No CSRF token yet on form-based routes; `SameSite=Lax` mitigates the most common attack vectors but a dedicated token would be a stronger production-grade defense.
- [ ] Hotel images are a single field for now; a real implementation would support multiple images per hotel (gallery, primary image for search results).
- [ ] No rate limiting on login.
- [ ] Search currently has limited demo data (a handful of hotels); search/filter logic is implemented and tested, but not yet backed by a large realistic dataset.
- [ ] Confirming or declining an experience request doesn't trigger any notification to the guest (they must check "My Experiences" manually). In production, this would trigger an email notification to the guest; out of scope for this project.
- [ ] No guest-facing way to cancel a pending experience request once submitted.
- [ ] Experience request price (`total_price`) is calculated and stored at request time to protect against the host later changing the experience's price while a request is still pending — but if a request is later modified, the price is not recalculated.
- [ ] `migrate_data.py` was a one-time script for the SQLite → Postgres data migration; not intended to be re-run against a populated Postgres database.