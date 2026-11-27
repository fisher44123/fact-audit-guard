<div align="center">

# 🛡️ Fact Audit Guard · 防 AI 幻觉交付审校器

**Zero-dependency deterministic fact & risk pre-publish auditor Skill for AI Agents.**  
在文章、研报、竞品分析或长文公开发布前，拦截**无来源统计数字**、**绝对化最高级违禁词**、**空口自证**与**未披露盲区**。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](scripts/audit_draft.py)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Stdlib%20Only)-success.svg)](#)
[![SkillHub](https://img.shields.io/badge/Tencent-SkillHub-0052D9.svg)](https://skillhub.cn/)
[![Alipay SkillPay](https://img.shields.io/badge/Alipay-SkillPay-1677FF.svg)](https://skillpay.alipay.com/)

[快速安装](#-快速安装) · [核心能力](#-为什么需要它) · [实测演示](#-实测效果对比) · [规则定制](#️-规则外置定制) · [进阶版](#-进阶云端服务)

</div>

---

## ✨ 为什么需要它

市面上大多数 AI 写作工具都在帮你**生成初稿**，但没有工具在内容**署上你的名字发布前**做最后一道确定性检查：

- ❌ AI 随手编造的「80 家厂商中 65 家存在故障」——没有来源编号；
- ❌ 毫无顾忌写出「全网最强」「唯一可靠」「100% 有效」——发布即踩合规红线；
- ❌ 把未验证或未检索的盲区悄悄抹平，伪装成完整结论；
- ❌ 只说「测试全部通过」，不附任何命令或路径凭证。

**Fact Audit Guard** 把能用代码确定性判定的规则全部收进本地 `audit_draft.py` + `rules.json`，不靠大模型主观“自己审自己”，直接输出可执行的 **`[BLOCK]` / `[FIX]` / `[NOTE]`** 三级修订清单与 **Open Questions 待查问题**。

---

## 🔍 核心核查矩阵

| 检查项 | 级别 | 机械判定逻辑（`rules.json` 可配） | 处理建议 |
| :--- | :---: | :--- | :--- |
| **统计数字溯源** | `BLOCK` | 扫描带计量单位（`个/条/项/次/元/%/万/家`）的数据附近是否有 `SRC-xxx` / URL / `[1]` 脚注（自动豁免日期、版本号与设计参数） | 补齐真实出处或删除精确数字 |
| **空口自证拦截** | `BLOCK` | 拦截无验证命令或路径支撑的「全部通过 / 已实锤 / 零误报」断言 | 补出实际执行命令与计数 |
| **最高级与越级词** | `FIX` | 检查「唯一 / 第一 / 最大 / 最强 / 100% / 彻底」所在段是否具备 ≥2 处来源支撑（自动豁免「第一步/第一名」等序数与否定语境） | 替换为限定范围的客观表述 |
| **覆盖边界与缺口** | `FIX` | 检查是否单列未覆盖范围、局限或 `Open Questions` 章节 | 显式列出尚待核实的开放问题 |
| **反向质疑推演** | `NOTE` | 检查是否提供 ≥3 条「如果核心假设错了最可能错在哪」的反向追问 | 补足反证思考防单边偏见 |

---

## 🚀 快速安装

### 方式一：兼容 `npx skills`（Claude Code / Codex / Cursor / Antigravity / WorkBuddy）

```bash
npx skills add fisher44123/fact-audit-guard
```

### 方式二：手动克隆本地立即试跑（零第三方依赖）

```bash
git clone https://github.com/fisher44123/fact-audit-guard.git
cd fact-audit-guard

# 对反例草稿运行严格检查（预期触发 BLOCK + FIX，退出码 1）
python scripts/audit_draft.py examples/bad_draft_demo.md --strict

# 对合规草稿运行检查（预期全绿 PASS，退出码 0）
python scripts/audit_draft.py examples/good_draft_demo.md --strict
```

---

## 📊 实测效果对比

运行 `python scripts/audit_draft.py examples/bad_draft_demo.md --strict` 实测输出：

```text
=== Fact Audit Guard ===
  [BLOCK] 统计数字带出处: 3 个统计量中 3 个无出处（100%）；如 L3「80」
  [BLOCK] 无裸露自证断言: 自称全部通过
  [FIX]   越级词 ≥2 处来源: 「100% 全部通过」
  [FIX]   最高级词汇合规: 「最强」
  [FIX]   覆盖边界/Open Questions: 缺失局限或 Open Questions 章节
  [NOTE]  反向质疑 ≥3 条: 当前 0 条
Summary: BLOCK=2, FIX/NOTE=4
```

对比修改后的 `examples/good_draft_demo.md`：

```text
=== Fact Audit Guard ===
  [PASS]  统计数字带出处: 0 个统计量中 0 个无出处（0%）
  [PASS]  无裸露自证断言: 通过
  [PASS]  越级词 ≥2 处来源: 通过
  [PASS]  最高级词汇合规: 通过
  [PASS]  覆盖边界/Open Questions: 已声明
  [PASS]  反向质疑 ≥3 条: 当前 3 条
Summary: BLOCK=0, FIX/NOTE=0
```

---

## ⚙️ 规则外置定制

所有词表、单位、豁免规则与硬拦分级均抽离在 [`rules.json`](rules.json) 中，无需修改 Python 代码即可按你的行业（金融 / 医疗 / 电商 / 技术研报）调整松紧度：
- `fail_on`：触发非零退出码的硬拦项（默认 `["numbers", "claims"]`）
- `superlative_words`：需要多源印证才能使用的绝对化词汇表
- `source_hint`：识别为有效引用的正则表达式模式

---

## 🔗 生态与进阶服务

- **腾讯 SkillHub 社区版**：已同步上架，支持国内一键发现与 WorkBuddy 安装；
- **支付宝 SkillPay 云端版**：已上架订阅制版（支持 **5 次免费试用**），适合需要免本地脚本配置、跨端开箱即用的个人与团队；
- **需要全链路多源采研 / 评论区水军清洗 / 本地全媒体知识库定制？** 欢迎提交 Issue 交流完整工程套件与私有部署方案。

## 📄 License

[MIT](LICENSE) © fisher44123
