import unittest
from kiigameEditorServer import server


class Tests(unittest.TestCase):

    def test_server_should_say_hello_world(self):
        self.assertEqual(server.Server.hello_world(),
                         'Hello World!')
