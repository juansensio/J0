from email.message import Message
from io import BytesIO
import unittest
from unittest.mock import MagicMock, patch

import client


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.handler_type = client.make_handler("192.168.1.123", "secret")

    def request(self, path, method="GET", browser=True):
        handler = object.__new__(self.handler_type)
        handler.path = path
        handler.headers = Message()
        if browser:
            handler.headers["X-Requested-With"] = "J0-control"
        handler.wfile = BytesIO()
        handler.send_response = lambda status: setattr(handler, "status", status)
        handler.response_headers = {}
        handler.send_header = lambda name, value: handler.response_headers.update({name: value})
        handler.end_headers = lambda: None
        getattr(handler, "do_" + method)()
        return handler.status, handler.wfile.getvalue(), handler.response_headers

    def test_page_is_open_and_contains_controls(self):
        status, body, headers = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        for command in client.COMMANDS:
            self.assertIn(f'data-command="{command}"'.encode(), body)
        self.assertNotIn(b"secret", body)

    def test_buttons_forward_only_allowed_commands(self):
        with patch.object(client, "send_command", return_value="Stopped") as send:
            status, body, _ = self.request("/api/stop", "POST")
            self.assertEqual((status, body), (200, b"Stopped"))
            send.assert_called_once_with("192.168.1.123", "secret", "stop")
            self.assertEqual(self.request("/api/reset", "POST")[0], 404)
            self.assertEqual(self.request("/api/forward", "POST", False)[0], 403)
            send.assert_called_once()

    def test_robot_connection_error_is_reported(self):
        with patch.object(client, "send_command", side_effect=OSError("offline")):
            status, body, _ = self.request("/api/forward", "POST")
        self.assertEqual(status, 502)
        self.assertIn(b"offline", body)

    def test_phone_url_uses_address_on_route_to_robot(self):
        probe = MagicMock()
        probe.__enter__.return_value = probe
        probe.getsockname.return_value = ("192.168.1.42", 54321)
        with patch.object(client.socket, "socket", return_value=probe):
            self.assertEqual(
                client.phone_url("192.168.1.123", 8000),
                "http://192.168.1.42:8000/",
            )
        probe.connect.assert_called_once_with(("192.168.1.123", 80))


if __name__ == "__main__":
    unittest.main()
