"""模型 HTTP 客户端：将环境配置和问题文本转换成一次接口调用。

调用方式依据仓库根目录 qianwneuse.md 的示例，以 httpx 直接发送 HTTP。
函数分工与数据流：
  Config.from_env() -> Config：读取、校验配置，密钥不显示在对象 repr 中。
  build_request(config, prompt) -> dict：只构造请求体，不发送请求。
  send_request(config, payload) -> dict：添加鉴权头、发送请求、处理网络错误。
  parse_response(data, expected_model) -> dict：检查响应，提取文本和统计信息。
main() 在 __main__.py 中，负责调用这些函数并把结果打印给用户。

本文件不主动运行测试。A.3 的测试在 tests/test_model_client.py 中，使用
httpx.MockTransport 替代真实网络、使用伪造 token，不消耗模型额度。
现有 11 个测试方法覆盖：
1. 请求地址、POST、鉴权/版本头、请求体、关闭 thinking、文本合并及密钥 repr 隐藏。
2. 返回模型与配置不一致时拒绝回答。
3. HTTP 302/401/429/503 转为错误（错误路径不输出响应正文）。
4. 无效 JSON。
5. 仅有 thinking，没有有效 text 正文。
6. 达到 max_tokens 且没有正文时提示截断。
7. 达到 max_tokens 但有部分正文时保留正文与停止原因。
8. 错误的响应对象、content 数组/块/text 类型以及缺少有效 usage。
9. 网络连接错误与读取超时。
10. 空白问题文本。
11. 环境变量读取、缺失配置、max_tokens 为零或非整数。

运行测试：python -m unittest discover -s tests -v（在 eqq/ 目录执行）。
真实调用另外验证当前服务的可用性；模拟测试不能证明真实 token 有效。
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv


class ModelError(Exception):
    """可安全展示的配置、网络或响应错误。"""


@dataclass(frozen=True)
class Config:
    """统一存放接口配置；frozen=True 防止创建后意外修改字段。"""
    base_url: str
    endpoint: str
    model: str
    token: str = field(repr=False)  # 打印 Config 对象时不显示密钥。
    version: str = "2023-06-01"
    max_tokens: int = 2048

    @property
    def url(self):
        """把服务地址与接口路径拼成 URL，可通过 config.url 直接访问。"""
        return self.base_url.rstrip("/") + self.endpoint

    @classmethod
    def from_env(cls):
        """创建配置对象；cls 指向 Config 类，不需要先实例化。"""
        # Docker 使用注入变量；宿主机使用仓库根目录 .env，不覆盖已有变量。
        # parents[2] 从 app/model_client.py 向上定位到仓库根目录。
        load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
        keys = ("QWEN_BASE_URL", "QWEN_ENDPOINT", "QWEN_MODEL",
                "QWEN_AUTH_TOKEN", "QWEN_ANTHROPIC_VERSION", "QWEN_MAX_TOKENS")
        values = {key: os.environ.get(key, "").strip() for key in keys}
        # 先拒绝缺失项，避免把空密钥或空地址发送给接口。
        missing = [key for key in keys if not values[key]]
        if missing:
            raise ModelError("缺少配置项：" + ", ".join(missing))
        # 检查地址和路径；错误信息只描述规则，不回显配置值。
        parsed = urlsplit(values["QWEN_BASE_URL"])
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise ModelError("QWEN_BASE_URL 必须是无凭证、查询参数的 HTTPS 地址。")
        if not values["QWEN_ENDPOINT"].startswith("/") or any(
            char in values["QWEN_ENDPOINT"] for char in "?#"
        ):
            raise ModelError("QWEN_ENDPOINT 必须是以 / 开头的接口路径。")
        try:
            # 环境变量都是字符串，输出预算需转为正整数。
            maximum = int(values["QWEN_MAX_TOKENS"])
        except ValueError:
            raise ModelError("QWEN_MAX_TOKENS 必须是正整数。") from None
        if maximum <= 0:
            raise ModelError("QWEN_MAX_TOKENS 必须是正整数。")
        return cls(values[keys[0]], values[keys[1]], values[keys[2]],
                   values[keys[3]], values[keys[4]], maximum)


def build_request(config, prompt):
    """A.1：构造最小单轮请求，不加入 system、历史或 Redis 状态。"""
    if not prompt.strip():
        raise ModelError("测试文本不能为空。")
    return {
        "model": config.model,
        "max_tokens": config.max_tokens,  # 输出上限，不是输入上下文窗口大小。
        "thinking": {"type": "disabled"},  # 使用中转文档验证过的关闭方式。
        "messages": [{"role": "user", "content": prompt}],  # 一条用户输入。
    }


def parse_response(data, expected_model):
    """解析 JSON 对象；成功时返回 text/model/stop_reason/usage 四项。"""
    if not isinstance(data, dict):
        raise ModelError("响应不是 JSON 对象。")
    # HTTP 成功也可能发生中转模型回落，必须核对返回的模型名。
    if data.get("model") != expected_model:
        raise ModelError("响应模型与配置模型不一致；停止接受本次回答。")
    blocks = data.get("content")
    if not isinstance(blocks, list):
        raise ModelError("响应 content 不是块数组。")
    parts = []
    # content 是块数组：只收集 text，忽略 thinking 和其他类型的块。
    for block in blocks:
        if not isinstance(block, dict):
            raise ModelError("响应内容块结构无效。")
        if block.get("type") == "text":
            if not isinstance(block.get("text"), str):
                raise ModelError("text 块缺少字符串正文。")
            parts.append(block["text"])
    text = "".join(parts)  # 同一回答可能被拆成多个 text 块，按原顺序拼接。
    if not text.strip():
        suffix = "（输出达到 max_tokens，可能被截断）" if data.get("stop_reason") == "max_tokens" else ""
        raise ModelError("响应没有有效 text 正文" + suffix + "。")
    # 保留统计与停止原因，供 CLI 判断是否完整，也便于后续观察成本。
    if not isinstance(data.get("usage"), dict) or not data.get("stop_reason"):
        raise ModelError("响应缺少 usage 或 stop_reason。")
    return {"text": text, "model": data["model"],
            "stop_reason": data["stop_reason"], "usage": data["usage"]}


def send_request(config, payload, client=None):
    """A.2：发送并解析一次请求；client 参数用于注入模拟网络客户端。"""
    # 密钥只放在真实请求头中；不要打印 headers。
    headers = {"content-type": "application/json",
               "authorization": "Bearer " + config.token,
               "anthropic-version": config.version}
    own_client = client is None
    if own_client:
        # 正常运行自行创建客户端；测试传入 MockTransport 客户端。
        # 不跟随重定向，避免把认证信息发送到新的目标地址。
        client = httpx.Client(timeout=60, follow_redirects=False)
    try:
        try:
            # json=payload 由 httpx 将字典编码成 JSON 请求体。
            response = client.post(config.url, headers=headers, json=payload)
        except httpx.TimeoutException:
            # from None 隐藏底层异常链，避免异常中携带敏感地址或信息。
            raise ModelError("模型请求超时（60 秒）；未自动重试。") from None
        except httpx.RequestError:
            raise ModelError("模型请求网络连接失败；未自动重试。") from None
        if not 200 <= response.status_code < 300:
            # 不输出服务端错误正文，防止意外回显凭证。
            raise ModelError(f"模型接口返回 HTTP {response.status_code}。")
        try:
            # HTTP 成功不代表正文一定是合法 JSON，还需单独解析。
            data = response.json()
        except ValueError:
            raise ModelError("模型接口返回无效 JSON。") from None
        return parse_response(data, config.model)
    finally:
        # 无论成功还是失败，都关闭自己创建的连接；外部传入的由调用方关闭。
        if own_client:
            client.close()
