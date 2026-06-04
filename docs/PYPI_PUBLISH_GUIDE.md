# ACR-QA PyPI Publish Guide

> **Status:** Workflow is ready. Three manual steps needed (one-time).
> After setup: `pip install acrqa && acrqa --help` works globally.

## One-time setup (Ahmed does this once)

### Step 1 — Create PyPI project

1. Go to https://pypi.org/manage/projects/ (sign in)
2. Click "Create a new project"
3. Name: `acrqa`
4. Verify the project at https://pypi.org/project/acrqa/

### Step 2 — Add Trusted Publisher (OIDC — no token needed)

1. On the `acrqa` PyPI project page → **Publishing**
2. Add a new trusted publisher:
   - **Owner:** `ahmed-145`
   - **Repository:** `ACR-QA`
   - **Workflow filename:** `pypi-publish.yml`
   - **Environment name:** `pypi`
3. Repeat for TestPyPI:
   - Go to https://test.pypi.org/manage/projects/
   - Same project name `acrqa`
   - Same trusted publisher but **Environment name:** `testpypi`

### Step 3 — Create GitHub Environments

In the GitHub repo → Settings → Environments:
1. Create environment named `testpypi` (no protection rules needed)
2. Create environment named `pypi` (add "Required reviewers" = yourself for safety)

## Publish

```bash
# Tag the current version (triggers the workflow)
git tag v5.0.0rc2
git push origin v5.0.0rc2
```

The workflow will:
1. Build sdist + wheel
2. Verify `acrqa --version` works on the wheel
3. Publish to TestPyPI (environment: testpypi)
4. Publish to PyPI (environment: pypi — you'll get a review request)

## Verify

```bash
pip install acrqa==5.0.0rc2
acrqa --version
# → ACR-QA v5.0.0rc2
acrqa --help
# → usage: acrqa [--target-dir DIR] [--sarif PATH] [--llm] [--fast] ...
```

## Notes

- The `acrqa` entry point is already in `pyproject.toml` (`[project.scripts]`)
- OIDC trusted publishing means no API tokens stored in GitHub secrets
- The workflow triggers only on `v*` tags (not every push)
- TestPyPI runs first; if it fails, PyPI is never touched
