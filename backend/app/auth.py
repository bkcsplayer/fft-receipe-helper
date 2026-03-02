import logging
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)

security = HTTPBasic()

# Hardcoded users per requirements
USERS = {
    "admin": "1q2w3e4R",
    "admin2": "1q2w3e4R"
}


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Validate HTTP Basic Auth credentials against hardcoded users."""
    username = credentials.username
    password = credentials.password

    if username not in USERS:
        logger.warning("Auth failed: Unknown user '%s'", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Use secure string comparison to prevent timing attacks
    expected_password = USERS[username]
    is_password_correct = secrets.compare_digest(
        password.encode("utf8"), expected_password.encode("utf8")
    )

    if not is_password_correct:
        logger.warning("Auth failed: Incorrect password for '%s'", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return username
