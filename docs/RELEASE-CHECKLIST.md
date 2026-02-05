# NEO-AIOS Release Checklist

Manual checklist for preparing and executing NEO-AIOS releases.

---

## Pre-Release Checks

### Code Quality

- [ ] All tests passing locally: `uv run pytest tests/`
- [ ] Coverage above 80%: `uv run pytest --cov=src/aios --cov-fail-under=80`
- [ ] mypy strict mode: `uv run mypy --strict src/`
- [ ] ruff no warnings: `uv run ruff check src/ tests/`
- [ ] ruff format check: `uv run ruff format --check src/ tests/`

### Security

- [ ] No hardcoded secrets in codebase
- [ ] All dependencies audited: `uv pip install pip-audit && uv run pip-audit`
- [ ] Security validators functional (< 1% false positives)
- [ ] `.env` and credentials not committed

### Documentation

- [ ] README.md is complete and accurate
- [ ] All public APIs documented
- [ ] CHANGELOG.md updated with release notes
- [ ] Agent catalog is current
- [ ] Architecture docs match implementation

### System Verification

- [ ] Agent identity isolation working
- [ ] Scope enforcement functional
- [ ] Session persistence working
- [ ] CLI commands functional: `neo-aios --help`
- [ ] All validators producing correct output

---

## Version Bump Procedure

### 1. Determine Version Number

Follow [Semantic Versioning](https://semver.org/):

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Breaking changes | MAJOR | 0.1.0 → 1.0.0 |
| New features | MINOR | 0.1.0 → 0.2.0 |
| Bug fixes | PATCH | 0.1.0 → 0.1.1 |
| Pre-release | PRE | 0.1.0-alpha.1 |

### 2. Update Version

```bash
# Edit pyproject.toml
# Change: version = "X.Y.Z"

# Verify
grep 'version = ' pyproject.toml
```

### 3. Update CHANGELOG.md

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Modified behavior description

### Fixed
- Bug fix description

### Security
- Security-related changes
```

### 4. Create Release Commit

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to X.Y.Z"
```

---

## Testing Requirements

### Unit Tests

All unit tests must pass:

```bash
uv run pytest tests/ -v
```

### Integration Tests

Run integration tests if available:

```bash
uv run pytest tests/ -v -m integration
```

### Manual Testing

- [ ] Fresh install works: `pip install dist/neo_aios-*.whl`
- [ ] CLI functional: `neo-aios --version`
- [ ] Import works: `python -c "import aios; print(aios.__version__)"`

### CI Verification

- [ ] CI pipeline passes on main branch
- [ ] All quality gates green
- [ ] Build artifacts generated correctly

---

## Release Execution

### 1. Final Verification

```bash
# Run full quality check
uv run ruff check src/ tests/
uv run mypy --strict src/
uv run pytest tests/ --cov=src/aios --cov-fail-under=80

# Build and verify
uv build
ls -la dist/
```

### 2. Create Git Tag

```bash
# Format: vX.Y.Z
git tag -a v1.0.0 -m "NEO-AIOS v1.0.0 - Initial Release"

# Verify tag
git show v1.0.0
```

### 3. Push Tag

```bash
# Push tag to trigger release workflow
git push origin v1.0.0
```

### 4. Monitor Release Pipeline

1. Go to GitHub Actions
2. Watch "Release" workflow
3. Verify all jobs complete successfully

### 5. Verify Release Artifacts

- [ ] GitHub Release created
- [ ] Release notes accurate
- [ ] Wheel file attached
- [ ] Source tarball attached
- [ ] PyPI package published (if applicable)

---

## Post-Release Tasks

### Immediate (Day 0)

- [ ] Verify PyPI installation: `pip install neo-aios==X.Y.Z`
- [ ] Check GitHub Release page
- [ ] Update documentation links if needed
- [ ] Announce release (if applicable)

### Short-term (Week 1)

- [ ] Monitor for issue reports
- [ ] Respond to user feedback
- [ ] Check download statistics

### Medium-term (Month 1)

- [ ] Collect user feedback
- [ ] Plan improvements for next version
- [ ] Update roadmap

---

## Rollback Procedure

If critical issues are found post-release:

### 1. Assess Severity

| Severity | Action |
|----------|--------|
| Low | Fix in next patch |
| Medium | Hot patch within 24h |
| Critical | Yank release + hotfix |

### 2. Yank from PyPI (if needed)

```bash
# Only for critical security issues
# This hides the release, doesn't delete
pip install twine
twine upload --skip-existing dist/*  # Upload fixed version first
# Then yank via PyPI web interface
```

### 3. Create Hotfix

```bash
# Create hotfix branch
git checkout -b hotfix/vX.Y.Z+1 vX.Y.Z

# Fix issue
# ... make changes ...

# Bump patch version
# Update CHANGELOG

# Commit and tag
git commit -m "fix: critical issue in vX.Y.Z"
git tag -a vX.Y.Z+1 -m "Hotfix release"
git push origin hotfix/vX.Y.Z+1 vX.Y.Z+1
```

---

## Quick Reference

### Version Checks

```bash
# Check current version
grep 'version = ' pyproject.toml

# Verify version in built package
python -c "import aios; print(aios.__version__)"
```

### Quality Commands

```bash
# Full quality suite
uv run ruff check src/ tests/ && \
uv run mypy --strict src/ && \
uv run pytest tests/ --cov=src/aios --cov-fail-under=80
```

### Release Commands

```bash
# Tag and push
git tag -a vX.Y.Z -m "NEO-AIOS vX.Y.Z"
git push origin vX.Y.Z
```

---

*Last Updated: 2026-02-05*
*NEO-AIOS Release Process v1.0*
