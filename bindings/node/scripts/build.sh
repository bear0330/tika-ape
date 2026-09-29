#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

script_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_root/.." && pwd)
cache_directory="$project_root/build/npm-cache"

mkdir -p "$cache_directory"
"$script_root/prepare.sh"
cd "$project_root"
npm pack --cache "$cache_directory"
