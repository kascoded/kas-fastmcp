#!/bin/bash
# Schema Sync Wrapper Script
# Makes it easier to run schema sync operations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/scripts/sync_schemas.py"

# Check if we're in a virtual environment or need to use uv
if command -v uv &> /dev/null && [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    # Use uv to run the script
    cd "$SCRIPT_DIR"
    exec uv run python scripts/sync_schemas.py "$@"
elif [ -n "$VIRTUAL_ENV" ]; then
    # Already in a virtual environment
    exec python "$SYNC_SCRIPT" "$@"
else
    # Try to activate venv if it exists
    if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
        source "$SCRIPT_DIR/.venv/bin/activate"
        exec python "$SYNC_SCRIPT" "$@"
    else
        # Fall back to system python
        exec python3 "$SYNC_SCRIPT" "$@"
    fi
fi
