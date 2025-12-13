"""Unit tests for Python license detection."""

import pytest
from unittest.mock import Mock, patch
from taglyatelle.slash_commands.check_licenses.license_python import PythonAdapter


@pytest.fixture
def python_adapter():
    """Create a PythonAdapter instance for testing."""
    return PythonAdapter()


class TestPythonAdapter:
    """Test PythonAdapter functionality."""

    def test_file_handlers_registration(self, python_adapter):
        """Test that file handlers are properly registered."""
        handlers = python_adapter.file_handlers
        assert "requirements.txt" in handlers
        assert "uv.lock" in handlers
        assert "poetry.lock" in handlers
        assert len(handlers) == 3

    def test_clean_license_text_short(self, python_adapter):
        """Test cleaning of short license text."""
        result = python_adapter._clean_license_text("MIT")
        assert result == "MIT"

    def test_clean_license_text_empty(self, python_adapter):
        """Test cleaning of empty license text."""
        assert python_adapter._clean_license_text("") == "Unknown"
        assert python_adapter._clean_license_text("   ") == "Unknown"
        assert python_adapter._clean_license_text(None) == "Unknown"

    def test_detect_bsd_3_clause_explicit(self, python_adapter):
        """Test detection of explicit BSD-3-Clause license."""
        lines = [
            "Copyright (c) 2023, Author",
            "BSD 3-Clause License",
            "Redistribution and use in source and binary forms",
        ]
        license_upper = "\n".join(lines).upper()
        result = python_adapter._detect_bsd_license(lines, license_upper)
        assert result == "BSD-3-Clause"

    def test_detect_bsd_3_clause_structural(self, python_adapter):
        """Test detection of BSD-3-Clause by structural markers."""
        lines = [
            "Copyright notice",
            "Some text",
        ]
        license_text = """
        Redistribution and use in source and binary forms, with or without
        modification, are permitted provided that the following conditions are met:

        1. Redistributions of source code must retain the above copyright notice
        2. Redistributions in binary form must reproduce the above copyright notice
        3. Neither the name of the copyright holder nor the names of its
           contributors may be used to endorse or promote products derived from
           this software without specific prior written permission.
        """
        license_upper = license_text.upper()
        result = python_adapter._detect_bsd_license(lines, license_upper)
        assert result == "BSD-3-Clause"

    def test_detect_bsd_2_clause(self, python_adapter):
        """Test detection of BSD-2-Clause license."""
        lines = [
            "BSD 2-Clause License",
            "Redistribution and use in source and binary forms",
        ]
        license_upper = "\n".join(lines).upper()
        result = python_adapter._detect_bsd_license(lines, license_upper)
        assert result == "BSD-2-Clause"

    def test_detect_bsd_generic(self, python_adapter):
        """Test detection of generic BSD license."""
        lines = [
            "BSD License",
            "Some redistribution text",
        ]
        license_upper = "\n".join(lines).upper()
        result = python_adapter._detect_bsd_license(lines, license_upper)
        assert result == "BSD License"

    def test_detect_mit_license(self, python_adapter):
        """Test detection of MIT license."""
        lines = [
            "MIT License",
            "Permission is hereby granted",
        ]
        result = python_adapter._detect_mit_license(lines)
        assert result is True

    def test_detect_mit_license_not_found(self, python_adapter):
        """Test MIT license not detected when not present."""
        lines = [
            "Apache License",
            "Version 2.0",
        ]
        result = python_adapter._detect_mit_license(lines)
        assert result is False

    def test_detect_gpl_v3(self, python_adapter):
        """Test detection of GPL-3.0 license."""
        license_text = "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007"
        result = python_adapter._detect_gpl_license(license_text.upper())
        assert result == "GPL-3.0"

    def test_detect_gpl_v2(self, python_adapter):
        """Test detection of GPL-2.0 license."""
        license_text = "GNU GENERAL PUBLIC LICENSE Version 2, June 1991"
        result = python_adapter._detect_gpl_license(license_text.upper())
        assert result == "GPL-2.0"

    def test_detect_gpl_generic(self, python_adapter):
        """Test detection of generic GPL license."""
        license_text = "GNU GENERAL PUBLIC LICENSE"
        result = python_adapter._detect_gpl_license(license_text.upper())
        assert result == "GPL"

    def test_clean_license_text_verbose_bsd(self, python_adapter):
        """Test cleaning of verbose BSD license text."""
        verbose_license = """BSD 3-Clause License

Copyright (c) 2023, Author Name
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
..."""
        result = python_adapter._clean_license_text(verbose_license)
        assert result == "BSD-3-Clause"

    def test_clean_license_text_verbose_mit(self, python_adapter):
        """Test cleaning of verbose MIT license text."""
        verbose_license = """MIT License

Copyright (c) 2023 Author

Permission is hereby granted, free of charge, to any person obtaining a copy
..."""
        result = python_adapter._clean_license_text(verbose_license)
        # The function returns the full text when it's under 200 chars
        assert "MIT" in result

    def test_clean_license_text_verbose_gpl(self, python_adapter):
        """Test cleaning of verbose GPL license text."""
        verbose_license = """GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc.
..."""
        result = python_adapter._clean_license_text(verbose_license)
        # The function returns the full text when it's under 200 chars
        assert "GNU GENERAL PUBLIC LICENSE" in result and "Version 3" in result

    def test_clean_license_text_first_line(self, python_adapter):
        """Test cleaning returns first line for unknown verbose licenses."""
        verbose_license = "Custom License Agreement\nLong text follows\n" * 50
        result = python_adapter._clean_license_text(verbose_license)
        assert result == "Custom License Agreement"
        assert len(result) <= 100

    @patch("urllib.request.urlopen")
    def test_get_license_from_pypi_success(self, mock_urlopen, python_adapter):
        """Test successful license retrieval from PyPI."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"info": {"license": "MIT"}}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = python_adapter._get_license_from_pypi("requests")
        assert result == "MIT"

    @patch("urllib.request.urlopen")
    def test_get_license_from_pypi_with_classifier(self, mock_urlopen, python_adapter):
        """Test license retrieval from PyPI using classifiers."""
        mock_response = Mock()
        mock_response.read.return_value = b"""{"info": {
            "license": "",
            "classifiers": ["License :: OSI Approved :: Apache Software License"]
        }}"""
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = python_adapter._get_license_from_pypi("package")
        assert result == "Apache Software License"

    @patch("urllib.request.urlopen")
    def test_get_license_from_pypi_unknown_license(self, mock_urlopen, python_adapter):
        """Test PyPI returns Unknown when license is UNKNOWN."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"info": {"license": "UNKNOWN"}}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = python_adapter._get_license_from_pypi("package")
        assert result == "Unknown"

    @patch("urllib.request.urlopen")
    def test_get_license_from_pypi_network_error(self, mock_urlopen, python_adapter):
        """Test PyPI returns Unknown on network error."""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        result = python_adapter._get_license_from_pypi("nonexistent-package")
        assert result == "Unknown"

    @patch("urllib.request.urlopen")
    def test_get_license_from_pypi_http_error(self, mock_urlopen, python_adapter):
        """Test PyPI returns Unknown on HTTP 404."""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 404, "Not Found", {}, None
        )

        result = python_adapter._get_license_from_pypi("nonexistent-package")
        assert result == "Unknown"

    @patch("taglyatelle.slash_commands.check_licenses.license_python.metadata.metadata")
    def test_get_metadata_from_installed_package(self, mock_metadata, python_adapter):
        """Test getting metadata from installed package."""
        mock_meta = Mock()
        mock_meta.get.return_value = "Apache-2.0"
        mock_metadata.return_value = mock_meta

        result = python_adapter._get_metadata("pytest")
        assert result == "Apache-2.0"

    @patch("taglyatelle.slash_commands.check_licenses.license_python.metadata.metadata")
    def test_get_metadata_with_license_expression(self, mock_metadata, python_adapter):
        """Test getting metadata using License-Expression field."""
        mock_meta = Mock()
        mock_meta.get.side_effect = lambda key: (
            None if key == "License" else "MIT OR Apache-2.0"
        )
        mock_metadata.return_value = mock_meta

        result = python_adapter._get_metadata("package")
        assert result == "MIT OR Apache-2.0"

    @patch("taglyatelle.slash_commands.check_licenses.license_python.metadata.metadata")
    def test_get_metadata_with_classifier(self, mock_metadata, python_adapter):
        """Test getting metadata using classifier."""
        mock_meta = Mock()
        mock_meta.get.side_effect = lambda key: None
        mock_meta.get_all.return_value = [
            "Development Status :: 5 - Production/Stable",
            "License :: OSI Approved :: MIT License",
        ]
        mock_metadata.return_value = mock_meta

        result = python_adapter._get_metadata("package")
        assert result == "MIT License"

    @patch("taglyatelle.slash_commands.check_licenses.license_python.metadata.metadata")
    @patch.object(PythonAdapter, "_get_license_from_pypi")
    def test_get_metadata_falls_back_to_pypi(
        self, mock_pypi, mock_metadata, python_adapter
    ):
        """Test fallback to PyPI when package not installed."""
        from importlib import metadata

        mock_metadata.side_effect = metadata.PackageNotFoundError
        mock_pypi.return_value = "MIT"

        result = python_adapter._get_metadata("unknown-package")
        assert result == "MIT"
        mock_pypi.assert_called_once_with("unknown-package")

    def test_parse_requirements_file_simple(self, python_adapter):
        """Test parsing simple requirements.txt file."""
        content = """requests==2.28.0
pytest>=7.0.0
black~=22.0"""

        with patch.object(
            python_adapter, "_get_metadata", side_effect=["Apache-2.0", "MIT", "MIT"]
        ):
            result = python_adapter.parse_requirements_file(content)

        assert len(result) == 3
        assert result[0] == {"package": "requests", "license": "Apache-2.0"}
        assert result[1] == {"package": "pytest", "license": "MIT"}
        assert result[2] == {"package": "black", "license": "MIT"}

    def test_parse_requirements_file_with_comments(self, python_adapter):
        """Test parsing requirements.txt with comments and blank lines."""
        content = """# Core dependencies
requests==2.28.0

# Testing
pytest>=7.0.0
# black~=22.0"""

        with patch.object(
            python_adapter, "_get_metadata", side_effect=["Apache-2.0", "MIT"]
        ):
            result = python_adapter.parse_requirements_file(content)

        assert len(result) == 2
        assert result[0] == {"package": "requests", "license": "Apache-2.0"}
        assert result[1] == {"package": "pytest", "license": "MIT"}

    def test_parse_requirements_file_with_extras(self, python_adapter):
        """Test parsing requirements.txt with package extras."""
        content = """requests[security]==2.28.0
pytest[dev]>=7.0.0"""

        with patch.object(
            python_adapter, "_get_metadata", side_effect=["Apache-2.0", "MIT"]
        ):
            result = python_adapter.parse_requirements_file(content)

        assert len(result) == 2
        assert result[0] == {"package": "requests[security]", "license": "Apache-2.0"}
        assert result[1] == {"package": "pytest[dev]", "license": "MIT"}

    def test_parse_lock_files_uv(self, python_adapter):
        """Test parsing uv.lock file."""
        content = """[[package]]
name = "requests"
version = "2.28.0"

[[package]]
name = "pytest"
version = "7.0.0"
"""

        with patch.object(
            python_adapter, "_get_metadata", side_effect=["Apache-2.0", "MIT"]
        ):
            result = python_adapter.parse_lock_files(content)

        assert len(result) == 2
        assert result[0] == {"package": "requests", "license": "Apache-2.0"}
        assert result[1] == {"package": "pytest", "license": "MIT"}

    def test_parse_lock_files_poetry(self, python_adapter):
        """Test parsing poetry.lock file."""
        content = """[[package]]
name = "black"
version = "22.0.0"

[[package]]
name = "flake8"
version = "5.0.0"
"""

        with patch.object(python_adapter, "_get_metadata", side_effect=["MIT", "MIT"]):
            result = python_adapter.parse_lock_files(content)

        assert len(result) == 2
        assert result[0] == {"package": "black", "license": "MIT"}
        assert result[1] == {"package": "flake8", "license": "MIT"}

    def test_parse_lock_files_empty_packages(self, python_adapter):
        """Test parsing lock file with no packages."""
        content = """[tool.poetry]
name = "test-project"
"""

        result = python_adapter.parse_lock_files(content)
        assert result == []

    def test_get_file_handlers(self, python_adapter):
        """Test getting file handlers."""
        handlers = python_adapter.file_handlers
        assert callable(handlers["requirements.txt"])
        assert callable(handlers["uv.lock"])
        assert callable(handlers["poetry.lock"])
