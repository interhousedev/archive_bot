from app.domain.error import AppError


class EMISError(AppError):
    """Base EMIS client error."""
    type = "EMIS System"
    description = "An error occurred while communicating with EMIS."


class EMISAuthError(EMISError):
    """Invalid credentials or expired/revoked access token."""
    description = "Authentication failed. Please check your EMIS login and password."


class EMISRequestError(EMISError):
    """Unexpected response from the EMIS API (non-auth related)."""
    description = "EMIS returned an unexpected response. Please try again later."
