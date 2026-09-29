#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
repository_root=$(CDPATH= cd -- "$project_root/../.." && pwd)
source_ape="$repository_root/tika.com"
package_ape="$project_root/src/tika_ape/bin/tika.com"

"$repository_root/scripts/prepare.sh"

mkdir -p "$project_root/src/tika_ape/bin"

if [ ! -f "$package_ape" ] || ! cmp -s "$source_ape" "$package_ape"; then
  cp "$source_ape" "$package_ape"
fi

mkdir -p "$project_root/tests/fixtures"
cp -R "$repository_root/tests/fixtures/." "$project_root/tests/fixtures"
