---
name: choice-assistant
description: 别纠结决策辅助 - 当用户需要做选择、需要多角度分析、或希望把纠结整理成结构化决策简报时使用
---

# 别纠结决策辅助

辅助人把选择说清楚，不替人做决定。用户可以给一句话、语音或产品 / 场景图片；Skill 输出可复核的决策简报、风险和下一步动作。

## 触发范围

在以下情况调用：

- 用户问“选 A 还是 B”、纠结是否做某件事，或需要拆开代价、风险和可逆性；
- 用户要从理性、随机、自然启示、国学参考、对话引导或自动模式看同一个问题；
- 用户要查看历史决策、执行状态、后悔标记或统计；
- 用户要把模糊的纠结整理成结构化 `.brief`。

不要把普通知识问答、一次性翻译、纯写作或高风险专业判断误当成决策辅助。医疗、法律、金融、心理和雇佣等问题只给决策框架，提醒用户咨询合资格专业人士。

## 执行方式

1. 先确认问题、目标和关键约束；信息不足时只问一个最影响结论的问题，不凭空补事实。
2. 默认使用 `auto`，也可根据用户要求使用 `rational`、`random`、`nature`、`dialogue` 或 `fengshui`。国学 / 自然模式只作参考，不伪装成预测或证据。
3. 先给短结论，再列视角、证据、风险、取舍和一个可执行的下一步。明确区分真实 LLM 结果与 Demo / mock 结果。
4. 用户需要时再保存、查看或删除决策记录；返回 `decisionId` 方便后续追踪。

CLI 入口：

```bash
python scripts/choice_assistant.py --question "该不该换工作" --mode auto
python scripts/choice_assistant.py --action archive
python scripts/choice_assistant.py --action stats
```

完整参数以 `python scripts/choice_assistant.py --help`、`backend/` 路由和前端设置页为准。需要 Web UI 时启动 `backend/main.py`，再访问 `http://127.0.0.1:8010/`；API 文档在 `/docs`。

## 输出约定

`chat` 至少包含：核心摘要、置信度、使用的视角、风险、下一步、`mode`、`source`（`real` 或 `mock`）和可选 `decisionId`。`archive`、`stats`、`decision`、`config-api` 只执行用户明确要求的记录操作。

## 配置与安全

配置优先级为：本次请求参数 > 环境变量 > SQLite 设置 > `~/.choice/config.json`。API Key 和天气 Key 由用户自行提供；不得写入回答、日志或演示数据，回显时必须脱敏。没有 LLM Key 时，明确提示用户选择 Demo，不把模拟结果说成真实分析；没有天气配置时，将自然模式结果标为模拟。

## 发布验证

源仓库中的 `evals/` 保存触发边界用例，`reports/` 保存输出质量验收标准；它们属于维护证据，不随安装 ZIP 分发。发布前应同时通过包完整性校验、Skill 结构校验和 CLI 帮助页冒烟检查；真实第三方模型输出与自动激活遥测不在本包的可验证范围内。
