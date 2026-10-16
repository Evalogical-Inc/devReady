import platform

from devready.models import Result, Status


def check_python() -> Result:
    # Reports the interpreter running DevReady; no subprocess needed.
    return Result(
        check_id="python.version",
        title="Python",
        status=Status.PASS,
        summary=f"{platform.python_version()} found",
    )
