"""Checks that the study's package imports."""

import jegadeesh_titman_momentum_india


class TestPackage:
    """Tests of the package as a whole."""

    def test_package_imports(self) -> None:
        """The package imports and has a docstring.

        Returns:
            None.
        """
        assert jegadeesh_titman_momentum_india.__doc__
