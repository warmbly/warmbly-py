# Contributing to warmbly-py

Thanks for your interest in improving the Warmbly Python SDK! This guide covers
everything you need to get a change merged.

## Code of Conduct

This project is governed by our [Code of Conduct](./CODE_OF_CONDUCT.md). By
participating you are expected to uphold it. Please report unacceptable
behavior to **team@warmbly.com**.

## Development setup

We use [uv](https://docs.astral.sh/uv/) and [nox](https://nox.thea.codes/), but
plain `pip` + `venv` works just as well.

```bash
git clone https://github.com/warmbly/warmbly-py
cd warmbly-py

# with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# or with pip
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"

# install the git hooks
pre-commit install
```

## Everyday commands

| Task | Command |
|---|---|
| Run the tests | `pytest` |
| Tests across every Python | `nox -s tests` |
| Lint | `ruff check src tests` |
| Format | `ruff format src tests` |
| Type-check | `mypy src tests` |
| All pre-commit hooks | `pre-commit run --all-files` |
| Build the docs | `mkdocs serve` |

`nox -s tests`, `nox -s lint`, and `nox -s typecheck` mirror exactly what CI runs.

## Making a change

1. **Branch** off `main`: `git switch -c feat/short-description`.
2. **Write code and tests.** New behavior needs tests; bug fixes need a
   regression test. The shipped package is held at 100% statement and branch
   coverage (`fail_under = 100`), so CI fails on any uncovered line.
3. **Keep types honest.** The SDK ships `py.typed`; everything must pass
   `mypy --strict`. No `httpx` type may appear in a public signature.
4. **Add a changelog fragment** (see below).
5. **Run the hooks**: `pre-commit run --all-files`.
6. **Open a PR.** The PR title must follow
   [Conventional Commits](https://www.conventionalcommits.org/) (e.g.
   `feat: add contacts.export`) — it becomes the squash-merge commit message.

## Changelog fragments (towncrier)

We assemble `CHANGELOG.md` at release time from news fragments, so changelog
edits never cause merge conflicts. Add one file per PR under `changelog/`:

```bash
echo "Add `client.contacts.export()`." > changelog/123.feature.md
```

The filename is `<issue-or-pr-number>.<type>.md`, where `<type>` is one of:
`feature`, `change`, `deprecation`, `removal`, `bugfix`, `security`, `doc`.

## Sign-off (DCO)

We use the [Developer Certificate of Origin](https://developercertificate.org/).
Sign off every commit (certifying you wrote the code or have the right to
contribute it):

```bash
git commit -s -m "feat: ..."
```

## Releasing (maintainers)

1. `towncrier build --version vX.Y.Z` to assemble the changelog.
2. Commit, then tag: `git tag vX.Y.Z && git push --tags`.
3. The release workflow builds, publishes to TestPyPI, then to PyPI via Trusted
   Publishing, and drafts a GitHub release. No API tokens are involved.

Versioning follows [SemVer 2.0.0](https://semver.org/). The public API is the
`warmbly.__all__` export set plus documented resource methods; underscore-prefixed
modules are private.
