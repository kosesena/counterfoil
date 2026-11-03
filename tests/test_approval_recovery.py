"""The same restart/approval protocol used by the opt-in sandbox evidence command."""

import pytest

from scripts.check_approval_recovery import CASES, run_case


@pytest.mark.parametrize('case', CASES)
def test_approval_and_recovery_protocol(case, tmp_path):
    result = run_case(case, 'fake', str(tmp_path / 'state.db'))
    assert result['passed'] and result['replayBlocked']
