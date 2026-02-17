# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for logger.py logging configuration."""

import logging

from scripts.logger import get_logger, setup_logger


class TestSetupLogger:
    """Test suite for setup_logger function."""

    def test_setup_logger_default_level(self):
        """Test logger setup with default INFO level."""
        logger = setup_logger("test_logger_default")

        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logger_custom_level_debug(self):
        """Test logger setup with DEBUG level."""
        logger = setup_logger("test_logger_debug", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_setup_logger_custom_level_warning(self):
        """Test logger setup with WARNING level."""
        logger = setup_logger("test_logger_warning", level="WARNING")

        assert logger.level == logging.WARNING

    def test_setup_logger_custom_level_error(self):
        """Test logger setup with ERROR level."""
        logger = setup_logger("test_logger_error", level="ERROR")

        assert logger.level == logging.ERROR

    def test_setup_logger_custom_level_critical(self):
        """Test logger setup with CRITICAL level."""
        logger = setup_logger("test_logger_critical", level="CRITICAL")

        assert logger.level == logging.CRITICAL

    def test_setup_logger_invalid_level_defaults_to_info(self):
        """Test logger setup with invalid level defaults to INFO."""
        logger = setup_logger("test_logger_invalid", level="INVALID")

        assert logger.level == logging.INFO

    def test_setup_logger_no_propagation(self):
        """Test that logger does not propagate to root logger."""
        logger = setup_logger("test_logger_no_propagate")

        assert logger.propagate is False

    def test_setup_logger_no_duplicate_handlers(self):
        """Test that multiple calls don't create duplicate handlers."""
        logger1 = setup_logger("test_logger_dup")
        handler_count = len(logger1.handlers)

        # Call again with same name
        logger2 = setup_logger("test_logger_dup")

        assert len(logger2.handlers) == handler_count


class TestGetLogger:
    """Test suite for get_logger convenience function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_get_logger")

        assert isinstance(logger, logging.Logger)

    def test_get_logger_uses_default_config(self):
        """Test that get_logger uses default INFO level."""
        logger = get_logger("test_get_logger_default")

        assert logger.level == logging.INFO
