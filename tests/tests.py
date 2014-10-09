import unittest
from kiigameEditorServer import server


class Tests(unittest.TestCase):

    def test_tests_should_work(self):
        self.assertEqual(True, True)

    def test_server_should_say_hello_world(self):
        self.assertEqual(server.hello_world(), 'Hello World!')
