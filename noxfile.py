"""Task automation for warmbly-py.

Run ``nox -l`` to list sessions. ``nox -s tests`` runs the test suite across
every supported Python; ``nox -s lint`` / ``nox -s typecheck`` mirror CI.
"""

from __future__ import annotations

import nox

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = ["lint", "typecheck", "tests"]

PYTHONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(python=PYTHONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with coverage."""
    session.install("-e", ".[oauth,test]")
    session.run("pytest", "--cov", "--cov-report=term-missing", *session.posargs)


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run Ruff lint and format checks."""
    session.install("ruff>=0.6")
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")


@nox.session(python="3.12")
def typecheck(session: nox.Session) -> None:
    """Run mypy in strict mode over the shipped package, as CI does.

    The test suite is kept lint-clean rather than strictly typed, and pointing
    mypy at it fails outright: `tests/conftest.py` and `tests/gateway/conftest.py`
    collide as one module name.
    """
    session.install("-e", ".[oauth,test]", "mypy>=1.11")
    session.run("mypy", "src")


@nox.session(python="3.12")
def docs(session: nox.Session) -> None:
    """Build the documentation site."""
    session.install("-e", ".[docs]")
    session.run("mkdocs", "build", "--strict")
