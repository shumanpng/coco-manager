#!/usr/bin/env bash
#
# init.sh — install coco-manager into a user's project.
#
# Usage:
#   bash /path/to/coco-manager/init.sh [<project-root>] [--notes-dir <path>]
#
# Default project-root is $PWD. Default notes-dir is <project-root>/notes.
# With a TTY and no --notes-dir, you are prompted once for the notes location.
#
# Idempotent: re-runs overwrite repo-owned locations (.claude/skills/, the
# .coco-manager/ namespace holding instructions/ + the offline site/ +
# co-working-setup.md, and the flat Makefile + scripts/) but never touch
# user-owned data dirs (worklogs/, planning/items/, state/items/, meeting/) or
# an existing meta.md.
# There is no --force flag: repo-owned overwrites are safe by design.

set -euo pipefail

usage() {
  sed -n '3,13p' "$0" | sed 's/^# \{0,1\}//'
}

# ----- locate self (the cloned coco-manager repo root) -----
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ----- argument parsing (no --force) -----
PROJECT_ROOT="$PWD"
NOTES_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --notes-dir) NOTES_DIR="${2:-}"; shift 2 ;;
    -h|--help)   usage; exit 0 ;;
    --*)         echo "Unknown flag: $1" >&2; exit 2 ;;
    *)           PROJECT_ROOT="$1"; shift ;;
  esac
done

# ----- resolve + validate project root -----
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "error: project root is not a directory: $PROJECT_ROOT" >&2
  exit 1
fi
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# Guard: the project must not be the repo itself (or a subdir of it) — otherwise
# init.sh would install into its own checkout.
case "$PROJECT_ROOT" in
  "$REPO"|"$REPO"/*)
    echo "error: run init.sh against your OWN project, not the repo checkout." >&2
    echo "       cd ~/code/your-project && bash \"$REPO/init.sh\"" >&2
    exit 1 ;;
esac

# ----- resolve notes dir (prompt only with a TTY; else default) -----
if [ -z "$NOTES_DIR" ]; then
  if [ -t 0 ]; then
    printf 'Notes directory [%s]: ' "$PROJECT_ROOT/notes"
    read -r NOTES_INPUT || true
    NOTES_DIR="${NOTES_INPUT:-$PROJECT_ROOT/notes}"
  else
    NOTES_DIR="$PROJECT_ROOT/notes"
    echo "No TTY — using default notes dir: $NOTES_DIR"
  fi
fi

# Expand a leading ~ and absolute-ize.
case "$NOTES_DIR" in
  "~")   NOTES_DIR="$HOME" ;;
  "~/"*) NOTES_DIR="$HOME/${NOTES_DIR#\~/}" ;;
esac
mkdir -p "$NOTES_DIR"
NOTES_DIR="$(cd "$NOTES_DIR" && pwd)"

if [ ! -w "$NOTES_DIR" ]; then
  echo "error: notes directory is not writable: $NOTES_DIR" >&2
  exit 1
fi

# Guard: notes dir must not live inside the repo (a re-run's clean-replace would
# then delete the repo's own instructions/ and scripts/).
case "$NOTES_DIR" in
  "$REPO"|"$REPO"/*)
    echo "error: your notes directory cannot be inside the repo ($REPO)." >&2
    echo "       Pick a directory in your own project instead." >&2
    exit 1 ;;
esac

# Repo-owned namespace + safety marker. init.sh keeps all repo-owned templates
# and docs under <notes-dir>/.coco-manager/, marked by a .marker file inside.
CM_DIR="$NOTES_DIR/.coco-manager"
MARKER="$CM_DIR/.marker"

# Legacy upgrade: earlier versions kept repo-owned files under the name
# .context-manager (first a file marker, then a directory, sometimes with
# instructions/ flat at the notes-dir root). Migrate any of those to the current
# .coco-manager/ layout.
LEGACY_UPGRADE=
if [ -e "$NOTES_DIR/.context-manager" ]; then
  rm -rf "$NOTES_DIR/.context-manager"
  LEGACY_UPGRADE=1
fi

# If the notes dir already holds repo-owned-looking content but has no marker,
# it was not created by init.sh — refuse to overwrite the user's own files.
# (scripts/ and Makefile stay flat at the root, so they remain in this check.)
if [ ! -f "$MARKER" ] && [ -z "$LEGACY_UPGRADE" ]; then
  for p in .coco-manager scripts Makefile; do
    if [ -e "$NOTES_DIR/$p" ]; then
      echo "error: '$NOTES_DIR/$p' already exists and this notes dir was not created by init.sh." >&2
      echo "       Choose an empty or new notes directory, or remove the conflicting file(s)." >&2
      exit 1
    fi
  done
fi

echo "Project root: $PROJECT_ROOT"
echo "Notes dir:    $NOTES_DIR"
if [ -f "$MARKER" ] || [ -n "$LEGACY_UPGRADE" ]; then
  echo "Existing install detected — re-running as idempotent update."
fi
echo

# ----- repo-owned: skills -> .claude/skills/ (keep meta.md AND the user's own) -
# .claude/skills/ may also hold the user's own skills. Remove only the entries WE
# installed on a prior run (recorded in the manifest) so upstream-removed skills
# don't linger, without ever deleting the user's own skills.
SKILLS_DEST="$PROJECT_ROOT/.claude/skills"
SKILLS_MANIFEST="$SKILLS_DEST/.coco-manager-skills"
mkdir -p "$SKILLS_DEST"
if [ -f "$SKILLS_MANIFEST" ]; then
  while IFS= read -r entry; do
    [ -n "$entry" ] && [ "$entry" != "meta.md" ] && rm -rf "$SKILLS_DEST/$entry"
  done < "$SKILLS_MANIFEST"
fi
cp -R "$REPO/skills/." "$SKILLS_DEST/"
# Record what we just installed (top-level entries of the repo's skills/) so the
# next run knows exactly which entries are ours to refresh.
: > "$SKILLS_MANIFEST"
for entry in "$REPO"/skills/*; do
  printf '%s\n' "$(basename "$entry")" >> "$SKILLS_MANIFEST"
done

# meta.md: seed from template ONLY if absent — never clobber the paths /setup wrote.
if [ ! -f "$SKILLS_DEST/meta.md" ]; then
  cp "$REPO/skills/meta.md.template" "$SKILLS_DEST/meta.md"
  echo "seeded  .claude/skills/meta.md (run /setup to fill in paths)"
else
  echo "kept    .claude/skills/meta.md (already configured)"
fi

# ----- repo-owned namespace: .coco-manager/ (instructions + reference docs) -
# One clearly-owned folder keeps these from colliding with the user's own files.
mkdir -p "$CM_DIR"
# Assert ownership BEFORE copying, so a run interrupted mid-copy still leaves a
# marker and the next run recognizes this as our own dir (not foreign content).
printf 'Managed by coco-manager init.sh. Safe to re-run init.sh.\n' > "$MARKER"
rm -rf "$CM_DIR/instructions"
cp -R "$REPO/instructions" "$CM_DIR/instructions"
rm -rf "$CM_DIR/site"
mkdir -p "$CM_DIR/site"
cp "$REPO"/*.html "$CM_DIR/site/"
cp "$REPO/styles.css" "$REPO/og-image.png" "$CM_DIR/site/"
cp "$REPO/co-working-setup.md" "$CM_DIR/co-working-setup.md"

# Legacy cleanup: drop the old flat instructions/ (now relocated under .coco-manager/).
if [ -n "$LEGACY_UPGRADE" ]; then
  rm -rf "$NOTES_DIR/instructions"
  echo "note: layout upgraded — templates moved to .coco-manager/; re-run /setup to update the 'instructions' path."
fi

# ----- repo-owned tooling: Makefile + scripts stay at the notes-dir root -------
# (the index Makefile resolves planning/items + state/items relative to itself).
cp "$REPO/tooling/Makefile" "$NOTES_DIR/Makefile"
rm -rf "$NOTES_DIR/scripts"
cp -R "$REPO/tooling/scripts" "$NOTES_DIR/scripts"

# ----- user-owned: data dirs (create if missing; never overwrite) ------------
for d in worklogs planning/items state/items meeting; do
  mkdir -p "$NOTES_DIR/$d"
done

cat <<EOF

Done.

Next steps:
  1. Open Claude Code in $PROJECT_ROOT
  2. Run /setup        (configure paths in meta.md)
  3. Run /new-worklog  (start your first session)

Tutorial (offline copy, always installed):        $CM_DIR/site/index.html
Co-working CLAUDE.md snippets (optional, opt-in):  $CM_DIR/co-working-setup.md
EOF
