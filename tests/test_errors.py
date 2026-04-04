from __future__ import annotations

import pytest

from hir.core.errors import (
    CommandExecutionError,
    DependencyMissingError,
    HIRError,
    ParseError,
    PrivilegeRequiredError,
    ReportExportError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        DependencyMissingError,
        PrivilegeRequiredError,
        ParseError,
        ReportExportError,
        CommandExecutionError,
    ],
)
def test_expected_errors_share_hir_error_base(error_type: type[HIRError]) -> None:
    error = error_type("boom")

    assert isinstance(error, HIRError)
    assert str(error) == "boom"
