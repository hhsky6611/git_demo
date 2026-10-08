"""命令行入口：负责接收你的问题、调用客户端，并展示结果。

在 eqq/ 下执行 python -m app 时，Python 会运行本文件。
main() 的执行顺序：
1. 解析问题文本和 --dry-run 参数；未提供问题时使用默认学习问题。
2. 调用 Config.from_env() 读取并检查配置。
3. 调用 build_request() 构造 JSON 请求体，打印鉴权已脱敏的请求概要。
4. dry-run 到此结束；正常模式调用 send_request() 发送一次真实请求。
5. 打印正文、响应模型、停止原因和 token usage；处理截断或调用错误。

本文件负责“怎样运行和展示”，model_client.py 负责“怎样调用接口”。
不保存历史、不操作 Redis，也不执行测试；测试通过 unittest 命令单独运行。
退出码：0 = 成功（或 dry-run 成功），1 = 失败，2 = 正文可能被截断。
"""

import argparse
import json
import sys

from .model_client import Config, ModelError, build_request, send_request


def main():
    """把命令行输入依次交给配置、请求构造和发送函数。"""
    # nargs='?' 表示问题文本可省略；store_true 表示带上开关时值为 True。
    parser = argparse.ArgumentParser(description="单次文本请求 CLI；--dry-run 只构造请求。")
    parser.add_argument("prompt", nargs="?", default="用一句话解释大语言模型对话中的上下文管理。")
    parser.add_argument("--dry-run", action="store_true", help="仅展示脱敏请求，不调用 API")
    args = parser.parse_args()
    try:
        # 第一步：拿到配置对象；第二步：拿到待发送的普通 Python 字典。
        config = Config.from_env()
        payload = build_request(config, args.prompt)
        # 这里打印的是另行构造的展示对象，真实 token 不在其中。
        # ensure_ascii=False 保留中文；indent=2 让 JSON 按层级缩进。
        print(json.dumps({"url": config.url, "method": "POST",
                          "config_source": "环境变量 / 仓库根目录 .env",
                          "headers": {"authorization": "Bearer [REDACTED]",
                                      "anthropic-version": config.version,
                                      "content-type": "application/json"},
                          "payload": payload}, ensure_ascii=False, indent=2))
        if args.dry_run:
            # A.1 可在此检查请求；不会发出网络请求或消耗模型额度。
            return 0
        # A.2：发送一次请求，客户端返回已经提取好的正文与统计信息。
        result = send_request(config, payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["stop_reason"] == "max_tokens":
            # 即便已有正文，也不能把达到输出上限当作完整回答。
            print("提示：输出达到 max_tokens，正文可能不完整。", file=sys.stderr)
            return 2
        return 0
    except ModelError as exc:
        # 客户端将预期错误转成安全的 ModelError，CLI 统一展示。
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    # 只有直接运行模块才调用 main；被其他文件 import 时不自动调用接口。
    # SystemExit 把 main 的返回值交给 shell，便于脚本判断是否成功。
    raise SystemExit(main())
