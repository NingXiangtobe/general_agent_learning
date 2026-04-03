# ⚙️ [Project Name]: general_agent_learning
The general agent assistant on the local machine
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-Native-green.svg)
![Architecture](https://img.shields.io/badge/Architecture-Clean-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Windows_Optimized-lightgrey.svg)

> **“干中学：通用Agent设计与实现”**

**general_agent_learning** 是一个基于 Python 与 LangChain 构建的本地化、重型多智能体（Multi-Agent）核心调度引擎。是面向用户本地的**通用自动化任务执行机器**。

它采用 **Serverless / MapReduce** 的设计哲学，通过严谨的 **DAG（有向无环图）** 任务拓扑、绝对的**物理级沙箱隔离**以及深度的 **系统命令级防御**，确保大模型在本地执行代码、读写文件、运行终端命令时的确定性、并发安全性与零污染。

---

## 🎯 核心架构哲学 (Why this project?)

市面上大多数 Agent 框架（如传统的开源终端助手）倾向于构建一个“单体大助理”，依赖大模型的注意力去维持上下文，极易陷入环境污染与并发灾难。

本项目走的是**工业级流水线路线**，基于Plan-Execute、React、self-Reflection范式编排：
1. **主控（Lead Engineer）绝对控盘**：主节点不写代码，只负责理解需求、拆解 `PLAN.md` 任务树、分发调度。
2. **工兵（Sub-agent）无状态执行**：工兵节点是“独立的一次性消耗品”，被扔进沙箱干活，确保资源隔离与上下文隔离。

---

## ✨ 核心特性 (Key Features)

### 🛡️ 1. 企业级物理沙箱与并发控制
* **Task-Level Sandbox**：为每一个子任务动态分配独立的物理目录，保证环境清洁、安全。
* **全局线程防冲突锁 (`FileLockManager`)**：彻底消灭多 Agent 并发读写同一个文件时的“交叉覆写（Dirty Write）”灾难。

### 🧠 2. DAG 拓扑与反射审查 (Reflection)
* **黑板驱动 (`PLAN.md`)**：主节点规划与派发、子节点执行。一切行动基于物理落盘的任务图。
* **最终审查机制**：Agent 试图提交任务前，会被强制打断并进行 `Reflection`，杜绝大模型“敷衍了事”或“未完结先退出”。

### 🔄 3. 动态记忆管线与防崩溃
* **热/冷状态分离**：`.agent_hot_state.json` 维持实时上下文，`.agent_audit.log` 记录底层追溯审计。
* **多级上下文紧缩**：具备 L1 微压缩与全局 LLM 摘要快照，管理上下文。
* **物理重置探针**：应用启动时自动嗅探未完成的遗留状态，提供**“无缝续跑”**或**“开启新任务”**的交互式分流。

### 📡 4. 后台异步支持
* **Background Manager**：支持将超长耗时任务剥离主线程（Daemon 守护执行），不阻塞主脑决策。

---

## 🏗️ 目录结构 (Clean Architecture)
项目严格遵循领域驱动设计（DDD）与关注点分离（SoC）：

```text
claude_code_mini/
├── main.py                     # 🚀 [入口] 终端交互、探针拦截与物理重置
├── core/
│   ├── config.py               # ⚙️ [基建] LLM实例、环境变量
│   └── locks.py                # 🔒 [基建] 全局单例物理并发锁
├── state/
│   ├── persistence.py          # 💾 [状态] 审计落盘、热记忆、沙箱归零协议
│   └── memory.py               # 🧠 [状态] Token估算、工具微压缩、LLM全局摘要压缩
├── services/
│   ├── skill_loader.py         # 📚 [服务] 静态技能库解析器
│   ├── todo_manager.py         # 📋 [服务] Todo 解析服务（已弃用）
│   └── background.py           # ⏳ [服务] 异步后台线程池与信箱队列调度
├── tools/
│   ├── file_ops.py             # 📁 [工具] 读、写、改及防崩溃乱码兜底
│   ├── os_cmd.py               # 💻 [工具] PowerShell 注入与高危拦截
│   ├── delegation.py           # 🚀 [工具] Sub-agent 实例化与并发派发
│   └── ... (web, plan, etc.)   # 🛠️ [工具] 原子化解耦工具群
└── agents/
    ├── prompts.py              # 📝 [提示词] 动态生成 Lead 与 Sub 系统指令
    └── coordinator.py          # 🔄 [代理] 核心事件循环 (Agent Loop)
```

## 🚀 快速上手 (Quick Start)
### 1. 环境准备
确保你的机器已安装 Python 3.11+，并克隆本仓库。

```Bash
git clone [https://github.com/your-username/your-repo.git](https://github.com/your-username/your-repo.git)
cd your-repo
```

### 2. 安装依赖
```Bash
pip install -r requirements.txt
```
### 3. 环境配置
在根目录创建 .env 文件，配置你的大模型 API与网络代理（可选）：

### 4. 启动
```Bash
python main.py
```

## 💡 最佳本地模型搭配指南 
由于本项目拥有极度严谨的工具调用栈（Tool Calling）和并发体系，建议采用异构双模型编排，压榨每一滴算力：

### 👑 主控节点 (Lead Coordinator)：

定位：全局路由与计划管理。

模型建议：Tool Calling、推理规划能力强

### 👷 工兵节点 (Sub-agent)：

定位：任务执行、沙箱内硬核代码攻坚。

模型建议：代码生成与执行能力强

## 📜 License
本项目采用 MIT License 开源许可。欢迎 Fork、提交 PR，一起学习。