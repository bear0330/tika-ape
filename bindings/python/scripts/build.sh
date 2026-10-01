#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

script_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_root/.." && pwd)
temporary_directory="$project_root/build/tmp"

mkdir -p "$temporary_directory"
TMPDIR="$temporary_directory" \
"$script_root/prepare.sh"
TMPDIR="$temporary_directory" python -m build "$project_root"
version=$(python -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["project"]["version"])' "$project_root/pyproject.toml")
python "$script_root/normalize_archive.py" \
  "$project_root/dist/tika_ape-$version-py3-none-any.whl" \
  "$project_root/dist/tika_ape-$version.tar.gz"
