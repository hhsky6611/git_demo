"""仅验证开发环境，不发送模型请求或打印配置值。"""

import importlib
import importlib.metadata
import os
import platform
import sys


def main():
    print(f"Python: {platform.python_version()}")
    for module, package in (
        ("anthropic", "anthropic"),
        ("httpx", "httpx"),
        ("redis", "redis"),
        ("dotenv", "python-dotenv"),
    ):
        importlib.import_module(module)
        print(f"依赖可导入: {package} {importlib.metadata.version(package)}")

    required = (
        "QWEN_BASE_URL", "QWEN_ENDPOINT", "QWEN_MODEL",
        "QWEN_AUTH_TOKEN", "QWEN_ANTHROPIC_VERSION", "QWEN_MAX_TOKENS",
        "REDIS_URL",
    )
    missing = []
    for key in required:
        present = bool(os.environ.get(key, "").strip())
        print(f"配置 {key}: {'已设置' if present else '缺失'}")
        if not present:
            missing.append(key)
    if missing:
        print("环境检查失败：缺少必需配置。", file=sys.stderr)
        return 1

    import redis

    try:
        client = redis.Redis.from_url(
            os.environ["REDIS_URL"], socket_connect_timeout=3, socket_timeout=3
        )
        client.ping()
        client.close()
    except redis.RedisError as exc:
        # 不打印异常正文，避免 URL 中的凭证被带出。
        print(f"Redis 检查失败：{type(exc).__name__}", file=sys.stderr)
        return 1
    print("Redis PING: 成功")
    print("环境检查通过；未调用模型 API。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
