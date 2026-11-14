import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from enge_spx.state import Store, SPXError
from enge_spx.workspace_language import apply_verified_exit, environment, mode, resolved, selection, verify


class LanguageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = Store(Path(temp.name) / 'data')
        self.engine = Mock(store=self.store)
        self.state = {'session': 'session', 'proxy': 'http://127.0.0.1:2080'}
        self.evidence = {'ip': '8.8.8.8', 'line_ip': '1.1.1.1'}

    def configure(self, mode='line'):
        self.store.write('settings.json', {**self.store.settings(), 'language_mode': mode})

    def test_opt_in_preserves_legacy_configuration_without_geo_requests(self):
        self.assertEqual(mode(self.store.settings()), 'unchanged')
        self.assertIsNone(apply_verified_exit(self.engine, self.state, self.evidence))
        self.assertEqual(environment(self.store.settings()), [])
        self.engine.docker.run.assert_not_called()

    def test_line_and_final_ip_are_distinct_and_bound_to_geo_response(self):
        for language_mode, address in [('line', '1.1.1.1'), ('exit', '8.8.8.8')]:
            self.configure(language_mode)
            self.engine.docker.run.return_value = json.dumps({'ip': address, 'country_code': 'JP'})
            value = apply_verified_exit(self.engine, self.state, self.evidence)
            self.assertEqual(value['locale'], 'ja_JP.UTF-8')
            self.assertEqual(value['source_ip'], address)
            self.assertEqual(self.engine.docker.run.call_args.args[-1], address)
            verify(self.engine, self.evidence)

    def test_missing_first_hop_unknown_country_and_wrong_ip_do_not_fall_back(self):
        self.configure()
        with self.assertRaises(SPXError):
            apply_verified_exit(self.engine, self.state, {'ip': '8.8.8.8'})
        self.engine.docker.run.assert_not_called()
        for value in ({'ip': '1.1.1.1', 'country_code': 'XX'}, {'ip': '8.8.8.8', 'country_code': 'US'}, {'ip': '1.1.1.1', 'country_code': []}):
            self.engine.docker.run.return_value = json.dumps(value)
            with self.assertRaises(SPXError):
                apply_verified_exit(self.engine, self.state, self.evidence)
        self.assertNotIn('environment_language', self.store.settings())

    def test_utf8_input_and_english_cli_messages_are_separate_from_browser_language(self):
        self.configure()
        language = {**selection('JP'), 'mode': 'line', 'source_ip': '1.1.1.1'}
        self.store.write('settings.json', {**self.store.settings(), 'environment_language': language})
        cli, browser = environment(self.store.settings()), environment(self.store.settings(), browser=True)
        self.assertIn('LANG=ja_JP.UTF-8', cli)
        self.assertIn('LC_ALL=', cli)
        self.assertIn('LC_MESSAGES=C', cli)
        self.assertIn('LC_ALL=ja_JP.UTF-8', browser)
        self.assertIn('LANGUAGE=ja', browser)
        with self.assertRaises(SPXError):
            verify(self.engine, {'ip': '8.8.8.8', 'line_ip': '9.9.9.9'})
        self.configure('unchanged')
        self.assertIn('LANG=en_US.UTF-8', environment(self.store.settings()))

    def test_tampered_locale_is_rejected(self):
        self.configure()
        self.store.write('settings.json', {**self.store.settings(), 'environment_language': {**selection('JP'), 'mode': 'line', 'locale': '../../home'}})
        with self.assertRaises(SPXError):
            resolved(self.store.settings())
