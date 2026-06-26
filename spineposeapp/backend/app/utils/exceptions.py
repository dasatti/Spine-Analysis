from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


def not_found(message: str = "Resource not found") -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", message)


def conflict(code: str, message: str) -> AppError:
    return AppError(status.HTTP_409_CONFLICT, code, message)


def unauthorized(message: str = "Invalid credentials") -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message)


def forbidden(message: str = "Account inactive") -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", message)
