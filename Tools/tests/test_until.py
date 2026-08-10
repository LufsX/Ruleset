import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import until


class UtilityTests(unittest.TestCase):
    def test_run_in_threads_preserves_result_order(self):
        results = until.run_in_threads([lambda: "first", lambda: "second"])

        self.assertEqual(results, ["first", "second"])

    def test_run_in_threads_propagates_worker_errors(self):
        def fail():
            raise RuntimeError("worker failed")

        with self.assertRaisesRegex(RuntimeError, "worker failed"):
            until.run_in_threads([lambda: None, fail])

    def test_clear_comment_respects_quotes_and_url_fragments(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.yaml"
            destination = Path(directory) / "clean.yaml"
            source.write_text(
                "# full comment\n"
                "key: value # inline comment\n"
                "quoted: \"value # kept\" # removed\n"
                "url: https://example.com/#fragment\n",
                encoding="utf-8",
            )

            until.clear_comment(str(source), str(destination))

            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "key: value\nquoted: \"value # kept\"\n"
                "url: https://example.com/#fragment\n",
            )

    @mock.patch("until.requests.get")
    def test_fetch_text_checks_status_and_uses_timeout(self, get):
        response = get.return_value
        response.text = "content"

        self.assertEqual(until.fetch_text("https://example.com/source"), "content")

        get.assert_called_once_with(
            "https://example.com/source", timeout=until.HTTP_TIMEOUT
        )
        response.raise_for_status.assert_called_once_with()

    @mock.patch("until.time.sleep")
    @mock.patch("until.requests.get")
    def test_fetch_text_retries_transient_request_errors(self, get, sleep):
        failed_response = mock.Mock()
        failed_response.raise_for_status.side_effect = until.requests.ConnectionError(
            "temporary failure"
        )
        successful_response = mock.Mock(text="content")
        get.side_effect = [failed_response, successful_response]

        self.assertEqual(until.fetch_text("https://example.com/source"), "content")

        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(0.5)

    @mock.patch("until.requests.post")
    def test_post_json_text_checks_status_and_uses_timeout(self, post):
        response = post.return_value
        response.text = "rendered"

        result = until.post_json_text(
            "https://example.com/render",
            headers={"Accept": "text/html"},
            payload={"text": "source"},
        )

        self.assertEqual(result, "rendered")
        post.assert_called_once_with(
            "https://example.com/render",
            headers={"Accept": "text/html"},
            json={"text": "source"},
            timeout=until.HTTP_TIMEOUT,
        )
        response.raise_for_status.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
