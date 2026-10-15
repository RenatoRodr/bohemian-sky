#!/bin/sh
# Rollback procedure placeholder: requires explicit target and human activation.
set -eu
cat <<'EOF'
Rollback is a human-operated procedure. Do not run against a live installation
without explicit approval and a verified backup.

1. Stop the v3 launcher in the isolated environment.
2. Restore the exact backed-up hook/config files and permissions.
3. Verify hashes against the pre-migration inventory.
4. Confirm the previous runtime is active and v3 is absent from the launch path.
5. Run the previous-version health checks and retain migration evidence.

This script changes no files.
EOF
