"""Unit tests for R license detection."""

import pytest
from unittest.mock import Mock, patch
from taglyatelle.slash_commands.check_licenses.license_r import RAdapter


@pytest.fixture
def r_adapter():
    """Create an RAdapter instance for testing."""
    return RAdapter()


class TestRAdapter:
    """Test RAdapter functionality."""

    def test_file_handlers_registration(self, r_adapter):
        """Test that file handlers are properly registered."""
        handlers = r_adapter.file_handlers
        assert "DESCRIPTION" in handlers
        assert "renv.lock" in handlers
        assert len(handlers) == 2

    def test_clean_license_text_short(self, r_adapter):
        """Test cleaning of short license text."""
        result = r_adapter._clean_license_text("MIT")
        assert result == "MIT"

    def test_clean_license_text_empty(self, r_adapter):
        """Test cleaning of empty license text."""
        assert r_adapter._clean_license_text("") == "Unknown"
        assert r_adapter._clean_license_text("   ") == "Unknown"
        assert r_adapter._clean_license_text(None) == "Unknown"

    def test_clean_license_text_with_file_license(self, r_adapter):
        """Test cleaning license text with 'file LICENSE' pattern."""
        result = r_adapter._clean_license_text("MIT + file LICENSE")
        assert result == "MIT"

    def test_clean_license_text_with_file_licence(self, r_adapter):
        """Test cleaning license text with 'file LICENCE' pattern (British spelling)."""
        result = r_adapter._clean_license_text("GPL-3 | file LICENCE")
        assert result == "GPL-3"

    def test_clean_license_text_only_file_license(self, r_adapter):
        """Test cleaning license text that is only 'file LICENSE'."""
        result = r_adapter._clean_license_text("file LICENSE")
        assert result == "Unknown"

    def test_clean_license_text_multiline_with_file(self, r_adapter):
        """Test cleaning multiline license with file reference."""
        license_text = """GPL-3
Part of the R package
+ file LICENSE"""
        result = r_adapter._clean_license_text(license_text)
        assert result.startswith("GPL-3")
        assert "file LICENSE" not in result

    def test_clean_license_text_verbose(self, r_adapter):
        """Test cleaning of verbose license text."""
        verbose_license = "MIT License " + "A" * 300
        result = r_adapter._clean_license_text(verbose_license)
        assert len(result) <= 200

    def test_clean_license_text_first_line_long(self, r_adapter):
        """Test that first line is truncated if too long."""
        long_first_line = "Custom License " + "B" * 300
        result = r_adapter._clean_license_text(long_first_line)
        assert len(result) <= 200

    @patch("urllib.request.urlopen")
    def test_get_license_from_cran_success(self, mock_urlopen, r_adapter):
        """Test successful license retrieval from CRAN."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"License": "GPL-3"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = r_adapter._get_license_from_cran("dplyr")
        assert result == "GPL-3"

    @patch("urllib.request.urlopen")
    def test_get_license_from_cran_empty_license(self, mock_urlopen, r_adapter):
        """Test CRAN returns Unknown when license is empty."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"License": ""}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = r_adapter._get_license_from_cran("package")
        assert result == "Unknown"

    @patch("urllib.request.urlopen")
    def test_get_license_from_cran_network_error(self, mock_urlopen, r_adapter):
        """Test CRAN returns Unknown on network error."""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        result = r_adapter._get_license_from_cran("nonexistent-package")
        assert result == "Unknown"

    @patch("urllib.request.urlopen")
    def test_get_license_from_cran_http_error(self, mock_urlopen, r_adapter):
        """Test CRAN returns Unknown on HTTP 404."""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 404, "Not Found", {}, None
        )

        result = r_adapter._get_license_from_cran("nonexistent-package")
        assert result == "Unknown"

    @patch("urllib.request.urlopen")
    def test_get_license_from_cran_invalid_json(self, mock_urlopen, r_adapter):
        """Test CRAN returns Unknown on invalid JSON."""
        mock_response = Mock()
        mock_response.read.return_value = b"Not valid JSON"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = r_adapter._get_license_from_cran("package")
        assert result == "Unknown"

    def test_parse_description_file_simple(self, r_adapter):
        """Test parsing simple DESCRIPTION file."""
        content = """Package: mypackage
Version: 1.0.0
License: MIT
Description: A test package
"""
        result = r_adapter.parse_description_file(content)

        assert len(result) == 1
        assert result[0] == {"package": "mypackage", "license": "MIT"}

    def test_parse_description_file_with_file_license(self, r_adapter):
        """Test parsing DESCRIPTION file with file LICENSE reference."""
        content = """Package: ggplot2
Version: 3.4.0
License: MIT + file LICENSE
Description: Create Elegant Data Visualisations
"""
        result = r_adapter.parse_description_file(content)

        assert len(result) == 1
        assert result[0] == {"package": "ggplot2", "license": "MIT"}

    def test_parse_description_file_multiline_license(self, r_adapter):
        """Test parsing DESCRIPTION file with multiline license."""
        content = """Package: testpkg
Version: 1.0.0
License: GPL-3 | file LICENSE
    Part of the R package ecosystem
Description: A test package
"""
        result = r_adapter.parse_description_file(content)

        assert len(result) == 1
        assert result[0]["package"] == "testpkg"
        assert "GPL-3" in result[0]["license"]
        assert "file LICENSE" not in result[0]["license"]

    def test_parse_description_file_no_license(self, r_adapter):
        """Test parsing DESCRIPTION file without license field."""
        content = """Package: nolicense
Version: 1.0.0
Description: A package without license
"""
        result = r_adapter.parse_description_file(content)

        assert len(result) == 1
        assert result[0] == {"package": "nolicense", "license": "Unknown"}

    def test_parse_description_file_no_package_name(self, r_adapter):
        """Test parsing DESCRIPTION file without package name."""
        content = """Version: 1.0.0
License: MIT
Description: A package without name
"""
        result = r_adapter.parse_description_file(content)

        assert len(result) == 1
        assert result[0] == {"package": "Unknown", "license": "MIT"}

    def test_parse_description_file_complex_license(self, r_adapter):
        """Test parsing DESCRIPTION file with complex license."""
        content = """Package: complexlic
Version: 1.0.0
License: GPL-2 | GPL-3
    This package is dual-licensed
Description: Complex licensing
"""
        result = r_adapter.parse_description_file(content)

        assert len(result) == 1
        assert result[0]["package"] == "complexlic"
        assert "GPL" in result[0]["license"]

    def test_parse_description_file_invalid_content(self, r_adapter):
        """Test parsing invalid DESCRIPTION content."""
        content = "Not a valid DESCRIPTION file format!"

        result = r_adapter.parse_description_file(content)

        # Should return a list with Unknown package
        assert len(result) == 1
        assert result[0]["package"] == "Unknown"

    @patch.object(RAdapter, "_get_license_from_cran")
    def test_parse_renv_lock_simple(self, mock_cran, r_adapter):
        """Test parsing simple renv.lock file."""
        content = """{
  "Packages": {
    "dplyr": {
      "Package": "dplyr",
      "Version": "1.1.0"
    },
    "ggplot2": {
      "Package": "ggplot2",
      "Version": "3.4.0"
    }
  }
}"""
        mock_cran.side_effect = ["GPL-3", "MIT"]

        result = r_adapter.parse_renv_lock(content)

        assert len(result) == 2
        assert result[0] == {"package": "dplyr", "license": "GPL-3"}
        assert result[1] == {"package": "ggplot2", "license": "MIT"}
        assert mock_cran.call_count == 2

    @patch.object(RAdapter, "_get_license_from_cran")
    def test_parse_renv_lock_empty_packages(self, mock_cran, r_adapter):
        """Test parsing renv.lock with no packages."""
        content = """{
  "Packages": {}
}"""

        result = r_adapter.parse_renv_lock(content)

        assert result == []
        mock_cran.assert_not_called()

    def test_parse_renv_lock_invalid_json(self, r_adapter):
        """Test parsing invalid JSON in renv.lock."""
        content = "Not valid JSON {{"

        result = r_adapter.parse_renv_lock(content)

        assert result == []

    def test_parse_renv_lock_missing_packages_key(self, r_adapter):
        """Test parsing renv.lock without Packages key."""
        content = """{
  "R": {
    "Version": "4.2.0"
  }
}"""

        result = r_adapter.parse_renv_lock(content)

        assert result == []

    @patch.object(RAdapter, "_get_license_from_cran")
    def test_parse_renv_lock_with_many_packages(self, mock_cran, r_adapter):
        """Test parsing renv.lock with multiple packages."""
        content = """{
  "Packages": {
    "pkg1": {"Package": "pkg1"},
    "pkg2": {"Package": "pkg2"},
    "pkg3": {"Package": "pkg3"},
    "pkg4": {"Package": "pkg4"}
  }
}"""
        mock_cran.side_effect = ["MIT", "GPL-2", "Apache-2.0", "BSD-3"]

        result = r_adapter.parse_renv_lock(content)

        assert len(result) == 4
        assert mock_cran.call_count == 4

    def test_get_file_handlers(self, r_adapter):
        """Test getting file handlers."""
        handlers = r_adapter.file_handlers
        assert callable(handlers["DESCRIPTION"])
        assert callable(handlers["renv.lock"])
