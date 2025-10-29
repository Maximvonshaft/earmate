# EarMate Visual Rule-Driven Scraping Framework

This repository contains the foundational components for a visual rule-driven web scraping system.

## 当前能力

- `RuleSchema` 描述采集规则，覆盖列表字段、分页、详情页、调度、去重与输出设置。
- `RuleExecutor` 基于标准库实现字段抽取、点击动作及分页逻辑，可通过自定义 `fetcher` 接入真实网络请求。
- `RuleRepository`/`RuleService` 提供规则的内存级 CRUD、启停与试跑封装，为后续 API 层奠定基础。
- `InMemoryScheduler` 基于优先队列实现即时/CRON 调度时间计算，便于集成任务队列或执行器。

## Development

项目使用 Python 标准库实现核心能力，开发时请确保 `src` 目录已加入 `PYTHONPATH`（测试夹具已自动完成）。

在提交代码前运行 `ruff check` 与 `pytest` 确认静态检查和单元测试均通过。
