"""Test the simplified consume behavior for different input types."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from ..consume import CACHED_DOWNLOADS_DIRECTORY, FixturesSource


class TestSimplifiedConsumeBehavior:
    """Test suite for the simplified consume behavior."""

    def test_fixtures_source_from_release_url_no_api_calls(self):
        """Test that direct release URLs do not make API calls for release page."""
        test_url = "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_develop.tar.gz"

        with patch("pytest_plugins.consume.consume.FixtureDownloader") as mock_downloader:
            mock_instance = MagicMock()
            mock_instance.download_and_extract.return_value = (False, Path("/tmp/test"))
            mock_downloader.return_value = mock_instance

            source = FixturesSource.from_release_url(test_url)

            # Verify no release page is set for direct URLs
            assert source.release_page == ""
            assert source.url == test_url
            assert source.input_option == test_url

    def test_fixtures_source_from_release_spec_makes_api_calls(self):
        """Test that release specs still make API calls and get release page."""
        test_spec = "stable@latest"

        with patch("pytest_plugins.consume.consume.get_release_url") as mock_get_url:
            mock_get_url.return_value = "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_stable.tar.gz"
            with patch("pytest_plugins.consume.consume.get_release_page_url") as mock_get_page:
                mock_get_page.return_value = (
                    "https://github.com/ethereum/execution-spec-tests/releases/tag/v3.0.0"
                )
                with patch("pytest_plugins.consume.consume.FixtureDownloader") as mock_downloader:
                    mock_instance = MagicMock()
                    mock_instance.download_and_extract.return_value = (False, Path("/tmp/test"))
                    mock_downloader.return_value = mock_instance

                    source = FixturesSource.from_release_spec(test_spec)

                    # Verify API calls were made and release page is set
                    mock_get_url.assert_called_once_with(test_spec)
                    mock_get_page.assert_called_once_with(
                        "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_stable.tar.gz"
                    )
                    assert (
                        source.release_page
                        == "https://github.com/ethereum/execution-spec-tests/releases/tag/v3.0.0"
                    )

    def test_fixtures_source_from_regular_url_no_release_page(self):
        """Test that regular URLs (non-GitHub) don't have release page."""
        test_url = "http://example.com/fixtures.tar.gz"

        with patch("pytest_plugins.consume.consume.FixtureDownloader") as mock_downloader:
            mock_instance = MagicMock()
            mock_instance.download_and_extract.return_value = (False, Path("/tmp/test"))
            mock_downloader.return_value = mock_instance

            source = FixturesSource.from_url(test_url)

            # Verify no release page for regular URLs
            assert source.release_page == ""
            assert source.url == test_url

    def test_output_formatting_without_release_page_for_direct_urls(self):
        """Test output formatting when release page is empty for direct URLs."""
        from unittest.mock import MagicMock

        from pytest import Config

        config = MagicMock(spec=Config)
        config.fixtures_source = MagicMock()
        config.fixtures_source.was_cached = False
        config.fixtures_source.is_local = False
        config.fixtures_source.path = Path("/tmp/test")
        config.fixtures_source.url = "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_develop.tar.gz"
        config.fixtures_source.release_page = ""  # Empty for direct URLs

        # Simulate the output generation logic from pytest_configure
        reason = ""
        if config.fixtures_source.was_cached:
            reason += "Fixtures already cached."
        elif not config.fixtures_source.is_local:
            reason += "Fixtures downloaded and cached."
        reason += f"\nPath: {config.fixtures_source.path}"
        reason += f"\nInput: {config.fixtures_source.url or config.fixtures_source.path}"
        if config.fixtures_source.release_page:
            reason += f"\nRelease page: {config.fixtures_source.release_page}"

        assert "Release page:" not in reason
        assert "Path:" in reason
        assert "Input:" in reason

    def test_output_formatting_with_release_page_for_specs(self):
        """Test output formatting when release page is present for release specs."""
        from unittest.mock import MagicMock

        from pytest import Config

        config = MagicMock(spec=Config)
        config.fixtures_source = MagicMock()
        config.fixtures_source.was_cached = False
        config.fixtures_source.is_local = False
        config.fixtures_source.path = Path("/tmp/test")
        config.fixtures_source.url = "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_stable.tar.gz"
        config.fixtures_source.release_page = (
            "https://github.com/ethereum/execution-spec-tests/releases/tag/v3.0.0"
        )

        # Simulate the output generation logic from pytest_configure
        reason = ""
        if config.fixtures_source.was_cached:
            reason += "Fixtures already cached."
        elif not config.fixtures_source.is_local:
            reason += "Fixtures downloaded and cached."
        reason += f"\nPath: {config.fixtures_source.path}"
        reason += f"\nInput: {config.fixtures_source.url or config.fixtures_source.path}"
        if config.fixtures_source.release_page:
            reason += f"\nRelease page: {config.fixtures_source.release_page}"

        assert (
            "Release page: https://github.com/ethereum/execution-spec-tests/releases/tag/v3.0.0"
            in reason
        )


class TestFixturesSourceFromInput:
    """Test the from_input method without no_api_calls parameter."""

    def test_from_input_handles_release_url(self):
        """Test that from_input properly handles release URLs."""
        test_url = "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_develop.tar.gz"

        with patch.object(FixturesSource, "from_release_url") as mock_from_release_url:
            mock_from_release_url.return_value = MagicMock()

            FixturesSource.from_input(test_url)

            mock_from_release_url.assert_called_once_with(test_url, CACHED_DOWNLOADS_DIRECTORY)

    def test_from_input_handles_release_spec(self):
        """Test that from_input properly handles release specs."""
        test_spec = "stable@latest"

        with patch.object(FixturesSource, "from_release_spec") as mock_from_release_spec:
            mock_from_release_spec.return_value = MagicMock()

            FixturesSource.from_input(test_spec)

            mock_from_release_spec.assert_called_once_with(test_spec, CACHED_DOWNLOADS_DIRECTORY)

    def test_from_input_handles_regular_url(self):
        """Test that from_input properly handles regular URLs."""
        test_url = "http://example.com/fixtures.tar.gz"

        with patch.object(FixturesSource, "from_url") as mock_from_url:
            mock_from_url.return_value = MagicMock()

            FixturesSource.from_input(test_url)

            mock_from_url.assert_called_once_with(test_url, CACHED_DOWNLOADS_DIRECTORY)
