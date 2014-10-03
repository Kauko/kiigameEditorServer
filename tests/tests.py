import unittest
from kiigameEditorServer import application


class Tests(unittest.TestCase):

    def test_server_should_say_hello_world(self):
        self.assertEqual(application.Server.hello_world(),
                         'Hello World!')
