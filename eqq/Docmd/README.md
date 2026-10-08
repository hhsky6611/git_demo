# eqq 项目说明

通过两个人物在指定场景下轮流对话，逐步学习模型 API、上下文管理、Redis 会话状态和摘要压缩。当前完成阶段 A：单次文本请求和离线模拟测试；尚未实现两人物对话。

## 目录与文档约定

```text
eqq/
  app/                    CLI、配置读取、HTTP 请求和响应解析
  tests/                  离线 API 模拟测试
  scripts/                环境检查脚本
  Docmd/                  全部项目 Markdown 文档
    README.md             项目说明与启动入口
    设计思路.md
    任务阶段.md
    任务进度.md
    问题存储.md
    环境复现.md
  Dockerfile
  compose.yaml
  requirements.txt
  .dockerignore
```

后续项目描述、实验说明和进度等 Markdown 文件统一放在 `eqq/Docmd/`。进度更新使用 `Docmd/任务进度.md`；问题登记使用 `Docmd/问题存储.md`，仍需用户明确要求写入问题。

## 运行阶段 A

在 `eqq/` 目录运行：

```bash
docker compose up -d
# A.1：只构造请求，鉴权字段脱敏，不发送 API 请求
docker compose exec dev python -m app --dry-run
# A.2：真实请求，消耗模型额度
docker compose exec dev python -m app
# 自定义测试文本
docker compose exec dev python -m app "用一句话解释大语言模型的上下文窗口。"
# A.3：离线测试，无真实 API 调用
docker compose exec dev python -m unittest discover -s tests -v
docker compose exec dev python scripts/check_environment.py
docker compose down
```

首次在新机器启动时使用 `docker compose up -d --build`。请求依据仓库根目录 `qianwneuse.md` 的 HTTP 示例，使用 `/v1/messages`、Bearer 鉴权、版本头及关闭 thinking 的参数。当前中转在本次实测中接受此格式，不据此推断其他服务或接口的兼容性。客户端使用 httpx，不调用 Anthropic SDK；所有接口参数从环境变量读取。环境复现与配置方式见 [环境复现.md](环境复现.md)。

命令行会显示请求文本与响应正文，测试时不要输入敏感内容。认证值不会打印；网络和 HTTP 错误不回显服务端正文。超时为 60 秒，不自动重试，不跟随重定向。退出码 0 表示成功，1 表示配置/调用/解析失败，2 表示有正文但达到输出上限。真实返回的模型名必须与配置一致，避免静默切换模型。

## 学习入口

- [设计思路](设计思路.md)：目标与架构。
- [任务阶段](任务阶段.md)：每个小任务的操作和验收。
- [任务进度](任务进度.md)：实际完成状态与验证记录。
- [问题存储](问题存储.md)：按用户要求登记的问题与解决过程。

后续功能代码均需中文注释，详见 [开发约定](开发约定.md)。B.1 已定义 [夕阳表白场景](B.1场景配置.md)，配置在 `app/scenario.py`，尚未接入对话运行。

通常一次只推进一个任务；阶段 A 按用户要求合并完成 A.1–A.3，当前下一任务为 B.2。
