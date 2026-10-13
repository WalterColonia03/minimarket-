"""Tests for the environment boundary used by S1-SEC-01."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.env import database_config, get_bool, load_dotenv


class EnvironmentConfigurationTests(SimpleTestCase):
    def test_dotenv_does_not_override_process_environment(self) -> None:
        with TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("EXISTING=file-value\nNEW=file-value\n", encoding="utf-8")

            with patch.dict(os.environ, {"EXISTING": "process-value"}, clear=True):
                load_dotenv(env_file)

                self.assertEqual(os.environ["EXISTING"], "process-value")
                self.assertEqual(os.environ["NEW"], "file-value")

    def test_invalid_boolean_is_rejected(self) -> None:
        with patch.dict(os.environ, {"FLAG": "maybe"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                get_bool("FLAG")

    def test_empty_database_url_uses_local_sqlite(self) -> None:
        config = database_config(None, "/tmp/r1-pmv")

        self.assertEqual(config["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(config["NAME"], "/tmp/r1-pmv/r1_pmv.sqlite3")

    def test_postgresql_url_is_parsed_without_logging_credentials(self) -> None:
        config = database_config("postgresql://app_user:local-only@db:5432/r1_pmv", "/tmp/r1-pmv")

        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["USER"], "app_user")
        self.assertEqual(config["PASSWORD"], "local-only")
        self.assertEqual(config["HOST"], "db")
        self.assertEqual(config["NAME"], "r1_pmv")

    def test_postgresql_url_decodes_percent_encoded_credentials(self) -> None:
        config = database_config(
            "postgresql://app%40user:pass%3Aword%40db%23safe@db:5432/r1_pmv",
            "/tmp/r1-pmv",
        )

        self.assertEqual(config["USER"], "app@user")
        self.assertEqual(config["PASSWORD"], "pass:word@db#safe")

    def test_database_url_rejects_non_postgresql_scheme(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            database_config("mysql://user:password@db/r1_pmv", "/tmp/r1-pmv")
