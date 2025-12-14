check:
    ruff check
    pyrefly check

test:
    python -m pytest

fmt:
    ruff format
    ruff check --fix
