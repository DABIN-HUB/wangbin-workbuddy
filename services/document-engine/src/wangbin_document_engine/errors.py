"""Public, stable error categories for local and Skill callers."""


class EngineError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.public_message = message


class SecurityViolation(EngineError):
    pass


class ParseFailure(EngineError):
    pass


class ExportFailure(EngineError):
    pass
