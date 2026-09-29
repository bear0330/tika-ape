#!/bin/sh
# SPDX-License-Identifier: Apache-2.0

set -eu

script_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$script_root/prepare.sh"
python "$script_root/../tests/test_tika_ape.py"
python "$script_root/../tests/test_host_services.py"
python "$script_root/../tests/test_awt_image_extraction.py"
python "$script_root/../tests/test_tika_python_compat.py"
python "$script_root/../tests/test_tika_capabilities.py"
