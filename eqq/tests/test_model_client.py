import json
import unittest
from unittest.mock import patch

import httpx

from app.model_client import Config, ModelError, build_request, send_request


class ModelClientTests(unittest.TestCase):
    def setUp(self):
        self.config = Config("https://example.test", "/v1/messages", "test-model", "fake-token")
        self.payload = build_request(self.config, "你好")
        self.data = {"model": "test-model", "stop_reason": "end_turn",
                     "usage": {"input_tokens": 10, "output_tokens": 3},
                     "content": [{"type": "thinking", "thinking": "不展示"},
                                 {"type": "text", "text": "你好"},
                                 {"type": "text", "text": "！"}]}

    def call(self, status=200, data=None, raw=None):
        def handler(request):
            self.assertEqual(str(request.url), self.config.url)
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.headers["authorization"], "Bearer fake-token")
            self.assertNotIn("x-api-key", request.headers)
            self.assertEqual(request.headers["anthropic-version"], "2023-06-01")
            self.assertEqual(json.loads(request.content), self.payload)
            if raw is not None:
                return httpx.Response(status, content=raw)
            return httpx.Response(status, json=self.data if data is None else data)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            return send_request(self.config, self.payload, client)

    def test_request_and_text_blocks(self):
        self.assertEqual(self.payload["thinking"], {"type": "disabled"})
        self.assertEqual(self.call()["text"], "你好！")
        self.assertNotIn("fake-token", repr(self.config))

    def test_model_mismatch(self):
        self.data["model"] = "fallback"
        with self.assertRaisesRegex(ModelError, "模型不一致"):
            self.call()

    def test_http_errors_do_not_echo_body(self):
        for status in (302, 401, 429, 503):
            with self.subTest(status=status), self.assertRaisesRegex(ModelError, f"HTTP {status}"):
                self.call(status, raw=b"fake-secret")

    def test_invalid_json(self):
        with self.assertRaisesRegex(ModelError, "无效 JSON"):
            self.call(raw=b"not json")

    def test_missing_text(self):
        self.data["content"] = [{"type": "thinking", "thinking": "内部内容"}]
        with self.assertRaisesRegex(ModelError, "没有有效 text"):
            self.call()

    def test_truncated_without_text(self):
        self.data.update(content=[], stop_reason="max_tokens")
        with self.assertRaisesRegex(ModelError, "截断"):
            self.call()

    def test_truncated_with_partial_text(self):
        self.data["stop_reason"] = "max_tokens"
        self.assertEqual(self.call()["stop_reason"], "max_tokens")

    def test_malformed_responses(self):
        for data in ([], {**self.data, "content": "wrong"},
                     {**self.data, "content": [None]},
                     {**self.data, "content": [{"type": "text", "text": 3}]},
                     {**self.data, "usage": None}):
            with self.subTest(data=data), self.assertRaises(ModelError):
                self.call(data=data)

    def test_network_errors(self):
        for error, message in ((httpx.ReadTimeout, "超时"), (httpx.ConnectError, "连接失败")):
            def handler(request):
                raise error("fake-secret", request=request)
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaisesRegex(ModelError, message):
                    send_request(self.config, self.payload, client)

    def test_empty_prompt(self):
        with self.assertRaises(ModelError):
            build_request(self.config, " ")

    def test_environment_validation(self):
        env = {"QWEN_BASE_URL": "https://example.test", "QWEN_ENDPOINT": "/v1/messages",
               "QWEN_MODEL": "test-model", "QWEN_AUTH_TOKEN": "fake-token",
               "QWEN_ANTHROPIC_VERSION": "2023-06-01", "QWEN_MAX_TOKENS": "128"}
        with patch("app.model_client.load_dotenv"), patch.dict("os.environ", env, clear=True):
            self.assertEqual(Config.from_env().max_tokens, 128)
            for invalid in ("0", "no-number"):
                with patch.dict("os.environ", {"QWEN_MAX_TOKENS": invalid}):
                    with self.assertRaises(ModelError):
                        Config.from_env()
        with patch("app.model_client.load_dotenv"), patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ModelError, "缺少配置项"):
                Config.from_env()


if __name__ == "__main__":
    unittest.main()
