#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
repository_root=$(CDPATH= cd -- "$project_root/../.." && pwd)

"$repository_root/scripts/prepare.sh"

mkdir -p "$project_root/src/bin"
cp "$repository_root/tika.com" "$project_root/src/bin/tika.com"

mkdir -p "$project_root/tests/fixtures"
cp -R "$repository_root/tests/fixtures/." "$project_root/tests/fixtures"
