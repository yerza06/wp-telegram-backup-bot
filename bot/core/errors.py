from __future__ import annotations


class BotDomainError(RuntimeError):
    user_message = "Ошибка выполнения операции."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.user_message)


class MissingUtilityError(BotDomainError):
    user_message = "Не найдена системная утилита."


class InvalidWordPressPathError(BotDomainError):
    user_message = "Неверный путь WordPress."


class BackupPathError(BotDomainError):
    user_message = "Недоступна папка бэкапов."


class InsufficientSpaceError(BotDomainError):
    user_message = "Недостаточно свободного места."


class ProcessExecutionError(BotDomainError):
    def __init__(self, message: str, *, returncode: int | None = None, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(message)


class MySQLDumpError(ProcessExecutionError):
    pass


class MySQLError(ProcessExecutionError):
    pass


class ArchiveError(BotDomainError):
    user_message = "Поврежденный или неверный архив."


class WpCliError(ProcessExecutionError):
    pass


class DiskCheckError(ProcessExecutionError):
    pass


class ChartBuildError(BotDomainError):
    user_message = "Не удалось построить график диска."
