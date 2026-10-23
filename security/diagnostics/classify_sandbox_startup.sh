#!/bin/bash

# Classify a pre-marker startup error without treating a generic permission
# error as proof that the intended profile denial occurred.
classify_sandbox_startup() {
    local stderr_path=$1
    if /usr/bin/grep -Eiq 'sandbox_apply|sandbox.*(apply|initializ|start).*failed|invalid active developer path|xcrun: error' "$stderr_path"; then
        printf '%s\n' 'HOST_FAILURE'
    elif /usr/bin/grep -Eiq 'Operation not permitted|Permission denied|Read-only file system' "$stderr_path"; then
        printf '%s\n' 'STARTUP_PERMISSION_ERROR'
    else
        printf '%s\n' 'STARTUP_FAILURE'
    fi
}
