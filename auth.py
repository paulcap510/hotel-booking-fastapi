import secrets
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash

from config import settings


password_hash = PasswordHash.recommended() # creates a password hasher using argon2 with the recommended settings



def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# --- Session-based auth (replaces JWT) ---
# In-memory store for now. Maps session_id -> {"user_id": ..., "expires_at": ...}
# NOTE: this resets every time the server restarts. A DB table or Redis
# would persist across restarts — worth upgrading later, fine for now.

sessions: dict[str, dict] = {}  #? setting the sessions variable to a dictionary that consistes of a string and another dictionary. `dict[str, dict]` here is a type hint

#? when we do -> str, it means the session ID that is returned is going to. be a str, correct?
def create_session(user_id: int) -> str:
    """Create a new session and return the session_id to put in a cookie."""
    session_id = secrets.token_urlsafe(32)  # random, unguessable string
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    sessions[session_id] = {"user_id": user_id, "expires_at": expires_at}
    return session_id




def get_user_id_from_session(session_id: str | None) -> int | None:
    """Look up a session_id and return the user_id if the session is valid."""

    if session_id is None:
        return None

    session = sessions.get(session_id)
    if session is None:
        return None

    if datetime.now(UTC) > session["expires_at"]:
        del sessions[session_id]  # clean up expired session
        return None

    return session["user_id"]


def delete_session(session_id: str | None) -> None:
    """Remove a session — used for logout."""
    if session_id in sessions:
        del sessions[session_id]

