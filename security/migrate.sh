#!/bin/sh
# Manual migration checklist helper. It intentionally does not install or activate anything.
set -eu
cat <<'EOF'
Security v3 migration is not automated by this script.

Required sequence:
1. Review and approve the versioned v3 policy, launcher, tests, and target paths.
2. Back up current hook/config files with metadata and hashes to an approved private location.
3. Build an isolated test account or VM; do not edit the live installation.
4. Install only into that isolated environment and run all positive/negative tests.
5. Human explicitly activates the reviewed configuration in the isolated environment.
6. Verify effective filesystem, process, network, connector, Git, identity, and audit/recovery enforcement.
7. Only after that evidence, separately approve any live migration.
8. Keep the backup and rollback artifact until post-install checks pass.

This helper changes no files and performs no installation.
EOF
