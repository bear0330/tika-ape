#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
repository_root=$(CDPATH= cd -- "$project_root/../.." && pwd)
source_config="$repository_root/tika-config.json"
package_config="$project_root/src/config/default.json"

"$repository_root/scripts/prepare.sh"

mkdir -p "$project_root/src/bin"
cp "$repository_root/tika.com" "$project_root/src/bin/tika.com"

mkdir -p "$project_root/src/config"

if [ ! -f "$package_config" ] || ! cmp -s "$source_config" "$package_config"; then
  cp "$source_config" "$package_config"
fi

mkdir -p "$project_root/tests/fixtures"
cp -R "$repository_root/tests/fixtures/." "$project_root/tests/fixtures"
