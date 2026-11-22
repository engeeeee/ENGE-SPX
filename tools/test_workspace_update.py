"""Run the targeted workspace, forwarding and terminal regressions."""
from pathlib import Path
import unittest


tests = str(Path(__file__).resolve().parents[1] / 'tests')
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for pattern in ('test_app_update_ui.py', 'test_workspace_ui.py', 'test_workspace_profiles.py', 'test_workspace_launch.py',
                'test_migration.py', 'test_line_security.py', 'test_terminal_preferences.py', 'test_terminal_rendering.py',
                'test_terminal_usability.py', 'test_tool_session.py', 'test_antigravity.py'):
    suite.addTests(loader.discover(tests, pattern=pattern))
raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
