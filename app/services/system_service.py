import subprocess


def run_command(cmd: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return (result.stdout + "\n" + result.stderr).strip()

    except subprocess.TimeoutExpired:
        return "Команда превысила время выполнения."

    except Exception as e:
        return f"Ошибка выполнения команды: {e}"