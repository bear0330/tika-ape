# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import shutil
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import tika_ape


def main() -> None:
    fixture_path = PROJECT_ROOT / 'tests' / 'fixtures' / 'sample.txt'
    external_fixture_path = PROJECT_ROOT.parents[1] / 'tests' / 'fixtures' / 'sample.txt'
    missing_path = PROJECT_ROOT / 'tests' / 'fixtures' / 'missing.txt'

    extracted = tika_ape.extract(fixture_path)
    text = tika_ape.extract_text(fixture_path)
    metadata = tika_ape.metadata(fixture_path)
    detected_type = tika_ape.detect(fixture_path)
    document = tika_ape.extract_json(fixture_path)
    external_text = tika_ape.extract_text(external_fixture_path)

    assert 'APEBind turns portable CLI applications' in extracted
    assert 'APEBind turns portable CLI applications' in text

    assert 'Content-Type: text/plain' in metadata
    assert detected_type == 'text/plain'

    assert document['Content-Type'].startswith('text/plain')
    assert 'APEBind turns portable CLI applications' in external_text

    with tempfile.TemporaryDirectory(dir=PROJECT_ROOT, prefix='fixture with spaces-') as directory:
        spaced_path = Path(directory) / 'sample document.txt'
        shutil.copyfile(fixture_path, spaced_path)

        spaced_text = tika_ape.extract_text(spaced_path)

    assert 'APEBind turns portable CLI applications' in spaced_text

    try:
        tika_ape.extract_text(missing_path)
    except FileNotFoundError as error:
        assert str(missing_path) in str(error)
    else:
        raise AssertionError('a missing local file unexpectedly reached Tika')


if __name__ == '__main__':
    main()
