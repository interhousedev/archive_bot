class AppError(Exception):
    """Base application error with a user-facing description and a system type label."""

    type: str = "System"
    description: str = "An unexpected error occurred."

    def __init__(self, description: str = None):
        self.description = description or self.__class__.description
        super().__init__(self.description)
