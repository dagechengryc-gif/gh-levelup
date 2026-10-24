# 评分细则

总分 = 基础 1000 + 成就加成 ≤100 = **1100**。

所有分档都是 `tier(value, steps)`：命中最高档位得分，不累加。

## 档案 Profile — 200

| 指标 | 分 | 判据 |
| --- | ---: | --- |
| 头像 | 25 | `avatarUrl` 非空（GitHub 会生成默认头像，所以这里只判断是否已设置） |
| 显示名 | 20 | `name` 非空 |
| 简介 | 30 | `bio` ≥10 字符得 30；1–9 字符得 15 |
| 外链 | 25 | `websiteUrl` 非空 |
| 地区 | 15 | `location` 非空 |
| 组织 | 15 | `company` 非空 |
| Profile README | 70 | 存在与 login **同名**的仓库 |

Profile README 单项 70 分，是整个模型里性价比最高的一格：新建一个仓库、写 20 行 Markdown，5 分钟。

## 代码资产 Code — 250

| 指标 | 分 | 分档 |
| --- | ---: | --- |
| 原创仓库数 | 145 | 1→30, 2→50, 3→70, 5→100, 8→125, 15→145 |
| 旗舰仓完整度 | 35 | README 15 + LICENSE 12 + Description 8 |
| CI | 25 | 任一仓库含 `.github/workflows/` |
| 测试 | 25 | 任一仓库含 `tests/` 或 `test/` |
| 语言多样性 | 20 | 1→5, 2→10, 3→15, 4+→20 |

"旗舰仓" = star 最多者，star 相同按完整度、再按最近推送时间排序。
fork、archived 都不计入原创仓库数。

## 活跃度 Activity — 250

| 指标 | 分 | 分档（近 365 天 contributions） |
| --- | ---: | --- |
| 近一年贡献 | 230 | 10→20, 50→60, 150→110, 300→160, 500→200, 800→230 |
| 近 30 天提交天数 | 20 | 5→5, 10→10, 20→20, 30→20 |

贡献数来自 `contributionsCollection.contributionCalendar`，与主页绿格一致（含私有贡献计数，若账号开启展示）。

## 协作 Collaboration — 200

| 指标 | 分 | 分档 |
| --- | ---: | --- |
| 已合并 PR | 170 | 1→30, 2→60, 5→90, 16→130, 64→170 |
| 代码评审 | 30 | 3→10, 10→20, 30→30 |

`merged PR` 用 `author:<login> is:pr is:merged` 搜索计数；`review` 用 `reviewed-by:<login> is:pr`。

## 影响力 Reach — 100

| 指标 | 分 | 分档 |
| --- | ---: | --- |
| Star 合计 | 85 | 3→15, 10→30, 16→45, 50→65, 150→85 |
| 关注者 | 15 | 3→5, 10→10, 50→15 |

## 成就 Achievements — 加成 100

每枚徽章 15 分，去重后封顶 100。已知徽章：
`quickdraw` `pull-shark` `yolo` `pair-extraordinaire` `galaxy-brain` `starstruck` `public-sponsor`。

GitHub 没有徽章 API，`levelup.api.parse_achievements()` 解析 profile 页里的
`achievements/<slug>/detail` 链接；页面结构变了就只会少算，不会报错。

## 等级线

| 分数 | 等级 |
| ---: | --- |
| 0 | L1 种子 Seed |
| 150 | L2 青铜 Bronze |
| 320 | L3 白银 Silver |
| 500 | L4 黄金 Gold |
| 680 | L5 铂金 Platinum |
| 820 | L6 钻石 Diamond |
| 900 | L7 王者 Legend |

## FAQ

**Q：为什么我的 star/follower 是 0，但我觉得自己很活跃？**
A：本模型只统计**公开**信息。私有仓库的 commit 只有在账号开启
"Contributions: private contributions" 后才会进入 contributions 计数，
仓库本身（数量、star）永远不进。

**Q：徽章抓不到怎么办？**
A：GitHub 没有徽章 API，只能解析 profile 页。页面结构变更时会静默返回空列表，
其它五个维度不受影响。用 `--no-achievements` 可以跳过这次请求。

**Q：1000 分是不是很难拿满？**
A：满格需要 800+ 次年贡献、64 个已合并 PR、150+ star。它是个坐标，不是目标；
先看 `gh-levelup next` 的前三条，那才是能立刻动手的部分。

**Q：能给别人刷分吗？**
A：不能。合并 PR、star、review 都发生在别人的仓库和别人的判断里，
本工具只读不改，也不提供任何写入 GitHub 的接口。
