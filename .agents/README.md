# Shared AI Context

This directory is the single source of repository-specific AI-agent context.

The root-level `.codex`, `.gemini`, and `.claude` entries are symlinks to this directory so agent-specific tools can read the same instructions without duplicating files.

Editable skills live under `skills/`. Exported skill packages live under `packages/`.

This directory is not runtime research code and should not be synced to the Raspberry Pi benchmark target.
