# plan.md
Goal: Upload deployment files for contract-cli.

## Proposed Changes
- Build the distributables (sdist, wheel) via `uv build`.
- Upload the deployment files based on user instruction (PyPI, GitHub Release, etc.).

## Verification Plan
- Verify package exists locally in `dist/`.
- Verify upload success message.
