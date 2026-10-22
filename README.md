<div align="center">

# gh-levelup

**把你的 GitHub 账号当角色面板来看：算分、定级、给出下一步任务。**

纯标准库 · 零依赖 · 一条命令 · 支持离线快照复跑

[![CI](https://github.com/dagechengryc-gif/gh-levelup/actions/workflows/ci.yml/badge.svg)](https://github.com/dagechengryc-gif/gh-levelup/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Deps](https://img.shields.io/badge/dependencies-0-brightgreen)](pyproject.toml)

</div>

---

## 它解决什么问题

"我 GitHub 太菜了，怎么练级？" 这句话的信息量是零。
真正的问题是：**你现在在第几级，差多少分，下一分从哪儿来。**

`gh-levelup` 把账号拆成 6 个维度、20 个可量化指标，算出一个 0–1100 的分数，
再按缺口大小排出一张任务清单——按收益从高到低。

```bash
pip install git+https://github.com/dagechengryc-gif/gh-levelup
gh-levelup audit -u your-name
```

```
==============================================================
  GITHUB CHARACTER SHEET  @your-name
==============================================================
  等级 L3 白银 Silver   412 / 1100
  进度条 ############............ 92/180
  距离下一级还差 88 分
  基础数据 仓库 3  star 4  followers 7  年贡献 168  30天活跃 12  连击 3  merged PR 6
  徽章 [pair-extraordinaire] [quickdraw] [yolo]
--------------------------------------------------------------
  档案 Profile          140/200  ##############........
    [ok] 头像                 25/25   有头像
    [ok] 一句话简介            30/30   34 字符
    [!!] 主页/社交链接          0/25   没有外链
--------------------------------------------------------------
  下一步任务（按收益排序）
    1. +145 把私有项目里可开源的部分抽成 3~5 个原创仓库
    2. +120 每天至少 1 次有意义的 commit（当前 168 次/年，目标 500+）
    3. +70  建 <login>/<login> 仓库并写 Profile README
==============================================================
```

## 安装

```bash
# 需要 gh CLI 已登录，或设置 GITHUB_TOKEN
gh auth login

git clone https://github.com/dagechengryc-gif/gh-levelup
cd gh-levelup
python3 -m pip install -e .
```

## 用法

```bash
gh-levelup audit              # 当前 gh 账号
gh-levelup audit -u torvalds  # 指定账号
gh-levelup next -u someone    # 只看任务清单
gh-levelup audit --markdown report.md --json > snap.json
```

| 参数 | 作用 |
| --- | --- |
| `-u/--user` | 目标账号，省略则用 `gh api user` |
| `--from-json` | 读离线快照，不联网（CI 里可复跑） |
| `--save-json` | 存快照，方便对比两周前后 |
| `--markdown` | 输出 Markdown 面板，可直接贴进 README |
| `--no-achievements` | 跳过徽章抓取，少一次请求 |

## 评分模型

六个维度，基础 1000 分 + 成就加成 100 分：

| 维度 | 上限 | 关键指标 |
| --- | ---: | --- |
| 档案 Profile | 200 | 头像、显示名、简介、外链、地区、组织、Profile README |
| 代码资产 Code | 250 | 原创仓库数、旗舰仓完整度、CI、测试、语言多样性 |
| 活跃度 Activity | 250 | 近一年贡献数、近 30 天提交天数 |
| 协作 Collaboration | 200 | 已合并 PR、代码评审次数 |
| 影响力 Reach | 100 | Star 合计、关注者 |
| 成就 Achievements | 100 | 徽章数量（每枚 15 分，上限 100） |

等级：`L1 种子 0` → `L2 青铜 150` → `L3 白银 320` → `L4 黄金 500` → `L5 铂金 680` → `L6 钻石 820` → `L7 王者 900`。

细到每一分的取整规则见 [docs/scoring.md](docs/scoring.md)。

## 设计取舍

- **分数只做导航，不做评判。** 每个指标都打印一句话理由，知道分数从哪来，才知道怎么改。
- **离线可复跑。** 抓取（网络）和评分（纯函数）分离，快照存成 JSON 就能在 CI 里回归。
- **零依赖。** 只用标准库，`python3 -m levelup` 就能跑，不用为一个小工具装半个生态。
- **徽章靠抓 HTML。** GitHub 没有徽章的公开 API，只能解析 profile 页；解析失败不影响其它维度。

## 开发

```bash
python3 -m unittest discover -s tests -t . -v
```

## 路线图

- [x] 角色面板、六维评分、任务清单
- [x] 离线快照 + Markdown 输出
- [ ] `gh-levelup diff old.json new.json`：两周战绩对比
- [ ] 团队版：一次审计整个组织成员
- [ ] 成就预测：还差几个 PR 能拿 Pull Shark

## 许可

[MIT](LICENSE)
