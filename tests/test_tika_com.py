# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKA = ROOT / 'tika.com'
SAMPLE = ROOT / 'tests' / 'fixtures' / 'sample.txt'


class TikaComTests(unittest.TestCase):
    def run_tika(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(TIKA), *arguments],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def test_help(self) -> None:
        result = self.run_tika('--help')

        self.assertIn('Apache Tika', result.stdout)

    def test_extracts_text_and_metadata(self) -> None:
        source = str(SAMPLE.relative_to(ROOT))
        text = self.run_tika('--text', source).stdout
        metadata = json.loads(self.run_tika('--json', source).stdout)
        media_type = self.run_tika('--detect', source).stdout.strip()

        self.assertIn('APEBind turns portable CLI applications', text)
        self.assertEqual('text/plain', media_type)
        self.assertTrue(metadata['Content-Type'].startswith('text/plain'))


if __name__ == '__main__':
    unittest.main()
