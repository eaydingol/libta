from pathlib import Path
import pytest
from libta.nta import *
from .helpers import *

src_dir = Path(__file__).parent
realizable_test_dir = src_dir / "testcases" / "path_realizable"
not_realizable_test_dir = src_dir / "testcases" / "path_not_realizable"


def get_realizable():
    return get_xmls(realizable_test_dir)


def get_not_realizable():
    return get_xmls(not_realizable_test_dir)


@pytest.mark.parametrize("test_filename", get_realizable())
def test_realizable(test_filename):
    nta = NTAHelper(test_filename, "nta")
    path = path_from_query_comment(nta)

    assert is_path_realizable(path)[0] == True


@pytest.mark.parametrize("test_filename", get_not_realizable())
def test_not_realizable(test_filename):
    nta = NTAHelper(test_filename, "nta")
    path = path_from_query_comment(nta)

    assert is_path_realizable(path)[0] == False
