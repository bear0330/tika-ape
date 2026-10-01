#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
repository_root=$(CDPATH= cd -- "$project_root/../.." && pwd)
source_ape="$repository_root/tika.com"
package_ape="$project_root/src/tika_ape/bin/tika.com"
source_config="$repository_root/tika-config.json"
package_config="$project_root/src/tika_ape/config/default.json"

"$repository_root/scripts/prepare.sh"

mkdir -p "$project_root/src/tika_ape/bin"
mkdir -p "$project_root/src/tika_ape/config"

if [ ! -f "$package_ape" ] || ! cmp -s "$source_ape" "$package_ape"; then
  cp "$source_ape" "$package_ape"
fi

if [ ! -f "$package_config" ] || ! cmp -s "$source_config" "$package_config"; then
  cp "$source_config" "$package_config"
fi

mkdir -p "$project_root/tests/fixtures"
cp -R "$repository_root/tests/fixtures/." "$project_root/tests/fixtures"
