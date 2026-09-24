import curses
import unittest
from unittest.mock import patch

import client


class FakeScreen:
    def __init__(self, keys):
        self.keys = iter(keys)

    def keypad(self, _enabled):
        pass

    def erase(self):
        pass

    def addstr(self, *_args):
        pass

    def refresh(self):
        pass

    def getmaxyx(self):
        return 24, 80

    def getch(self):
        return next(self.keys)


class ClientTest(unittest.TestCase):
    def test_arrow_keys_and_quit_stop_robot(self):
        keys = [curses.KEY_UP, curses.KEY_LEFT, curses.KEY_DOWN,
                curses.KEY_RIGHT, ord(" "), ord("q")]
        with patch.object(client.curses, "curs_set"), patch.object(
            client, "send_command", return_value="OK"
        ) as send:
            client.control(FakeScreen(keys), "192.168.1.123", "secret")

        self.assertEqual(
            [call.args[2] for call in send.call_args_list],
            ["forward", "left", "backward", "right", "stop", "stop"],
        )


if __name__ == "__main__":
    unittest.main()
