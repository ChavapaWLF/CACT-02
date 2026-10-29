#!/usr/bin/env bash
set -euo pipefail

# Resolve paths relative to this script, not the caller's working directory.
test_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if (( $# > 1 )); then
    echo "Usage: $0 [compiler]" >&2
    exit 2
fi
exec python3 "$test_dir/test_pr1.py" \
    --compiler "${1:-$test_dir/../build/compiler}" --suite samples --verbose
