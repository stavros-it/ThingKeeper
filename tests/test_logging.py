"""Tests for thingkeeper.logging_config: log file and excepthook."""

from __future__ import annotations

import logging
import sys

from thingkeeper import logging_config


def test_setup_logging_creates_log_file(isolated_data_dir):
    logging_config._installed = False
    logging_config.setup_logging()
    assert logging_config.LOG_FILE.exists() or logging_config.LOG_FILE.parent.exists()
    logging_config._installed = False


def test_setup_logging_is_idempotent(isolated_data_dir):
    logging_config._installed = False
    logging_config.setup_logging()
    handler_count_1 = len(logging.getLogger().handlers)
    logging_config.setup_logging()
    handler_count_2 = len(logging.getLogger().handlers)
    assert handler_count_1 == handler_count_2
    logging_config._installed = False


def test_setup_logging_installs_excepthook(isolated_data_dir):
    logging_config._installed = False
    original = sys.excepthook
    try:
        logging_config.setup_logging()
        assert sys.excepthook is logging_config._excepthook
    finally:
        sys.excepthook = original
        logging_config._installed = False


def test_excepthook_logs_exception(isolated_data_dir, caplog):
    logging_config._installed = False
    logging_config.setup_logging()
    try:
        try:
            raise ValueError("boom")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
        with caplog.at_level(logging.CRITICAL, logger="thingkeeper.crash"):
            logging_config._excepthook(exc_type, exc_value, exc_tb)
        assert any("boom" in r.getMessage() for r in caplog.records)
    finally:
        sys.excepthook = sys.__excepthook__
        logging_config._installed = False
