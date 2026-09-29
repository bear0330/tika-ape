#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

"$repository_root/scripts/prepare.sh"
python "$repository_root/tests/test_tika_com.py"
