import logging
import subprocess

logger = logging.getLogger(__name__)


def run_command(command: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Команда выполнена, но ничего не вернула."
    except subprocess.TimeoutExpired:
        return "Команда выполнялась слишком долго."
    except Exception as e:
        logger.exception("Command failed")
        return f"Ошибка выполнения команды: {e}"
