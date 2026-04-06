---
name: horde-init
description: >
  Initialize a project for full Claude Code capabilities: creates CLAUDE.md (via /init),
  initializes git repository, and creates a GitHub remote. Ensures ultraplan and other
  remote features work. Use when starting work in a new or un-initialized project directory,
  or when /ultraplan fails with "Background tasks require a git repository."
---

# Horde Init

Initialize any project directory for full Claude Code capabilities in one command. Creates CLAUDE.md, initializes git, and sets up a GitHub remote — unlocking ultraplan and all remote features.

## Quick Start

```bash
User: "/horde-init"
# → Detects missing pieces, creates git repo, GitHub remote, CLAUDE.md
# → Reports ultraplan readiness

User: "/horde-init --public"
# → Same, but GitHub repo is public instead of private

User: "/horde-init --skip-github"
# → Git + CLAUDE.md only, no GitHub remote (ultraplan still needs a remote)
```

## When to Use

**Use this skill when:**
- Starting work in a new project directory
- `/ultraplan` fails with "Background tasks require a git repository"
- A project has code but no git repo or CLAUDE.md
- You need to quickly bootstrap a project for full Claude Code features

**Don't use when:**
- Project already has git + GitHub remote + CLAUDE.md (nothing to do)
- You only want CLAUDE.md without git (use `/init` directly)

## Workflow

```
/horde-init
├── Pre-flight checks
│   ├── Is gh CLI installed and authenticated?
│   ├── Does .git/ exist?
│   ├── Does a remote origin exist?
│   └── Does CLAUDE.md exist?
│
├── Step 1: Git Repository
│   ├── .git/ exists → Skip, report "Git repo already initialized"
│   └── .git/ missing →
│       ├── git init
│       └── Create .gitignore (detect stack, use sensible defaults)
│
├── Step 2: GitHub Remote
│   ├── --skip-github flag → Skip
│   ├── Remote exists → Skip, report "Remote already configured: <url>"
│   └── No remote →
│       ├── Derive repo name from directory name
│       ├── Ask user to confirm: repo name, visibility (private default)
│       ├── gh repo create <owner>/<name> --private --source . --push
│       └── If no commits yet, create initial commit first
│
├── Step 3: CLAUDE.md
│   ├── CLAUDE.md exists → Ask: regenerate or keep?
│   │   ├── Keep → Skip
│   │   └── Regenerate → Run /init
│   └── CLAUDE.md missing → Run /init to generate it
│
├── Step 4: Initial Commit (if needed)
│   ├── Check for uncommitted CLAUDE.md or .gitignore
│   └── git add CLAUDE.md .gitignore && git commit
│
└── Step 5: Verification
    ├── git rev-parse --is-inside-work-tree → ✓
    ├── git remote get-url origin → ✓ <url>
    ├── ls CLAUDE.md → ✓
    └── "Ultraplan ready — you can now use /ultraplan"
```

## Pre-Flight Checks

Before starting, verify prerequisites:

```bash
# Check gh CLI is installed
which gh || echo "MISSING: Install GitHub CLI — brew install gh"

# Check gh is authenticated
gh auth status || echo "MISSING: Run 'gh auth login' to authenticate"

# Check current state
git rev-parse --is-inside-work-tree 2>/dev/null  # git repo?
git remote get-url origin 2>/dev/null             # remote?
test -f CLAUDE.md && echo "CLAUDE.md exists"      # CLAUDE.md?
```

**If gh CLI is missing or not authenticated:**
```
GitHub CLI (gh) is required for creating a GitHub remote.

To install:  brew install gh
To login:    gh auth login

You can also run with --skip-github to skip GitHub setup,
but note that /ultraplan requires a remote repository.
```

Instruct the user to run the auth command themselves — do NOT run `gh auth login` on their behalf (it's an interactive login flow).

## Step 1: Git Repository

```bash
# Check if git repo exists
if git rev-parse --is-inside-work-tree 2>/dev/null; then
    echo "Git repo already initialized"
else
    git init
    echo "Git repository initialized"
fi
```

### .gitignore Generation

If no `.gitignore` exists, generate one based on detected stack:

| Detection | .gitignore Includes |
|-----------|-------------------|
| `package.json` exists | `node_modules/`, `.next/`, `dist/`, `.env`, `.env.local` |
| `pyproject.toml` or `requirements.txt` | `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env` |
| `Cargo.toml` | `target/`, `.env` |
| `go.mod` | `vendor/` (if not committed), `.env` |
| None detected | Minimal: `.env`, `.DS_Store`, `*.log` |

Always include in every `.gitignore`:
```
.env
.env.local
.DS_Store
*.log
```

**Never overwrite an existing `.gitignore`** — only create if missing.

## Step 2: GitHub Remote

**This step requires explicit user confirmation** — creating a GitHub repo is a visible external action.

### Confirmation Prompt

```
No GitHub remote found. Create one?

  Repository: <gh-username>/<directory-name>
  Visibility: Private (use --public to change)
  Action:     gh repo create <name> --private --source . --push

Create this repository? (yes/no/rename)
```

If user says "rename", ask for the desired repo name.

### Execution

```bash
# Ensure at least one commit exists before pushing
if ! git log --oneline -1 2>/dev/null; then
    git add -A
    git commit -m "Initial commit

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
fi

# Create GitHub repo (private by default)
gh repo create <name> --private --source . --push

# Or if --public flag:
gh repo create <name> --public --source . --push
```

### Edge Cases

- **Directory name has spaces/special chars**: sanitize to lowercase kebab-case for repo name
- **Repo name already taken on GitHub**: `gh repo create` will error — present the error and ask user for an alternative name
- **User not owner of the org**: if the directory path suggests an org, ask which GitHub owner to use

## Step 3: CLAUDE.md

### If CLAUDE.md is missing

Run the built-in `/init` command to generate it. The `/init` command analyzes the project and creates a context-appropriate CLAUDE.md:

```
No CLAUDE.md found. Running /init to generate one...
```

Invoke via: let Claude's built-in `/init` behavior handle this — read the project structure, detect the stack, and generate CLAUDE.md content. Write the file using the Write tool.

The generated CLAUDE.md should follow the standard format observed in this workspace:
- **Overview** section (1-2 sentences)
- **Commands** section (dev, build, test, lint commands from package.json/Makefile/pyproject.toml)
- **Architecture** section (key files, patterns, data flow)
- Follow patterns from existing CLAUDE.md files in the workspace (see `/Users/kublai/projects/CLAUDE.md` for style reference)

### If CLAUDE.md exists

Ask the user:
```
CLAUDE.md already exists. What would you like to do?
1. Keep existing (skip)
2. Regenerate from scratch
3. Append/update with current project state
```

## Step 4: Initial Commit

After all setup, if there are new files (CLAUDE.md, .gitignore) that haven't been committed:

```bash
# Stage only the files we created
git add CLAUDE.md .gitignore

# Commit
git commit -m "chore: initialize project with CLAUDE.md and .gitignore

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Push if remote exists
git remote get-url origin 2>/dev/null && git push -u origin main
```

**Important:** Only stage files created by this skill (CLAUDE.md, .gitignore). Do NOT run `git add -A` on existing project files without asking — the user may have files they don't want committed yet.

## Step 5: Verification & Report

After all steps complete, present a status report:

```
horde-init complete!

  Git repository:  ✓ initialized
  GitHub remote:   ✓ https://github.com/<user>/<repo>
  CLAUDE.md:       ✓ generated (423 lines)
  .gitignore:      ✓ created (Node.js + general)
  Initial commit:  ✓ pushed to origin/main

  Ultraplan:       ✓ READY — you can now use /ultraplan
```

Or if something was skipped:

```
horde-init complete!

  Git repository:  ✓ already existed
  GitHub remote:   ⊘ skipped (--skip-github)
  CLAUDE.md:       ✓ already existed (kept)
  .gitignore:      ✓ already existed

  Ultraplan:       ✗ NOT READY — requires GitHub remote
                   Run /horde-init again without --skip-github
```

## Flags

| Flag | Effect |
|------|--------|
| `--public` | Create GitHub repo as public (default: private) |
| `--skip-github` | Skip GitHub remote creation (git + CLAUDE.md only) |
| `--skip-init` | Skip CLAUDE.md generation (git + GitHub only) |
| `--force` | Regenerate CLAUDE.md even if it exists |

## Error Handling

| Error | Recovery |
|-------|----------|
| `gh: command not found` | Tell user: `brew install gh` then retry |
| `gh auth` not logged in | Tell user: run `! gh auth login` in prompt |
| Repo name taken on GitHub | Ask user for alternative name |
| `git init` fails (permissions) | Report error, suggest checking directory permissions |
| `/init` produces empty CLAUDE.md | Fall back to minimal template based on detected stack |
| Push fails (no commits) | Create initial commit first, then retry push |
| Push fails (branch name) | Try both `main` and `master`: `git branch -M main && git push` |

## Integration with Horde Ecosystem

After `horde-init` completes, the project is ready for:

- **`/ultraplan`** — remote deep-thinking sessions (requires git + remote)
- **`/horde-plan`** — structured implementation planning (works with or without git, but ultraplan tier requires it)
- **`/horde-implement`** — plan execution
- **`/ship-it`** — test, commit, deploy workflow

**Recommended first-run sequence for a new project:**
```
/horde-init          → bootstrap git + GitHub + CLAUDE.md
/horde-plan          → plan the implementation (ultraplan available for complex work)
/horde-implement     → execute the plan
```
