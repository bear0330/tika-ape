#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

script_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$script_root/prepare.sh"
node "$script_root/../tests/test_tika_ape.mjs"
node "$script_root/../tests/test_host_services.mjs"
node "$script_root/../tests/test_legacy.mjs"
