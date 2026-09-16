"""Public API errors; internal details belong only in the server log."""


class ApiError(Exception):
    status = 400
    public_message = 'Ongeldig verzoek.'


class Unauthorized(ApiError):
    status = 401
    public_message = 'Inloggen is vereist.'


class Forbidden(ApiError):
    status = 403
    public_message = 'Geen toegang.'


class NotFound(ApiError):
    status = 404
    public_message = 'Niet gevonden.'


class Conflict(ApiError):
    status = 409
    public_message = 'De gegevens zijn intussen gewijzigd. Laad de pagina opnieuw.'


class InvalidRequest(ApiError):
    pass
