# Repository Workflow

## Feature development

- Keep the default branch (`main`) read-only in the main worktree. Do not develop
  features or fixes directly on it.
- Use one sibling Git worktree and one dedicated `feature/*`, `fix/*`, or
  `refactor/*` branch per task. Personal worktree automation lives in
  `$manage-worktree`.
- After implementation and the relevant tests are complete, stage only the files
  that belong to the feature, commit on the task branch, then push and open a
  pull request against `main` only when explicitly asked.
- Never include secrets, `.env`, personal runtime configuration, or local backup
  files in a commit or pull request.
