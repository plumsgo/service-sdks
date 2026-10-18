"""AI Text SDK errors. These are not HTTP exceptions; callers map them."""


class AiTextError(Exception):
    """A call to the text generation service failed."""

    def __init__(self, status_code: int, detail) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))
