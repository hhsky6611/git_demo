# eqq 项目说明

通过两个人物在指定场景下轮流对话，逐步学习模型 API、上下文管理、Redis 会话状态和摘要压缩。当前仅完成环境准备与最小项目骨架。

## 目录与文档约定

```text
eqq/
  app/                    Python 应用包与占位入口
  tests/                  后续测试目录（目前只有占位文件）
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

## 运行占位命令

在 `eqq/` 目录运行：

```bash
docker compose up -d
docker compose exec dev python -m app
docker compose exec dev python scripts/check_environment.py
docker compose down
```

首次在新机器启动时使用 `docker compose up -d --build`。占位命令只输出项目状态，不读取密钥、调用模型或写入 Redis。环境复现与配置方式见 [环境复现.md](环境复现.md)。

宿主机也可在 `eqq/` 目录运行 `python3 -B -m app` 检查入口，但后续依赖和真实学习任务统一使用 Docker 环境。

## 学习入口

- [设计思路](设计思路.md)：目标与架构。
- [任务阶段](任务阶段.md)：每个小任务的操作和验收。
- [任务进度](任务进度.md)：实际完成状态与验证记录。
- [问题存储](问题存储.md)：按用户要求登记的问题与解决过程。

一次只推进一个任务，当前下一任务为 A.1。
