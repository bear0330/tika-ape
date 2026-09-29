#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
target_path="$repository_root/tika.com"
version=${TIKA_APE_VERSION:-}
force_download=${TIKA_APE_FORCE_DOWNLOAD:-0}

if [ -f "$target_path" ] && [ "$force_download" != "1" ]; then
  printf 'Using cached %s\n' "$target_path"
  exit 0
fi

if [ -n "$version" ]; then
  download_url="https://github.com/bear0330/tika-ape/releases/download/$version/tika.com"
else
  download_url='https://github.com/bear0330/tika-ape/releases/latest/download/tika.com'
fi

temporary_path="$target_path.download"
printf 'Downloading %s\n' "$download_url"
curl --fail --location --retry 3 --output "$temporary_path" "$download_url"

if [ ! -s "$temporary_path" ]; then
  printf '%s\n' 'Downloaded tika.com is empty' >&2
  exit 1
fi

mv -f "$temporary_path" "$target_path"
chmod +x "$target_path"
