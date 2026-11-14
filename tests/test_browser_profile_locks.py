import json
import unittest
from unittest.mock import Mock

from enge_spx.browser_profile_locks import prepare
from enge_spx.state import SPXError


class ProfileLockTests(unittest.TestCase):
    def test_only_new_browser_using_this_volume_can_recover_links(self):
        engine = Mock()
        obj = {'Id': 'a' * 64}
        engine.docker.run.side_effect = [obj['Id'], json.dumps({'schema': 1, 'removed': 3})]
        prepare(engine, obj, 'owned-profile')
        engine.owned.assert_called_once_with(obj, 'browser')
        self.assertEqual(engine.docker.run.call_args.args[:3], ('exec', obj['Id'], 'python3'))

    def test_shared_or_unproven_volume_is_never_modified(self):
        for users in ('', 'a' * 64 + '\n' + 'b' * 64, 'invalid'):
            engine = Mock()
            engine.docker.run.return_value = users
            with self.assertRaises(SPXError):
                prepare(engine, {'Id': 'a' * 64}, 'owned-profile')
            self.assertEqual(engine.docker.run.call_count, 1)
