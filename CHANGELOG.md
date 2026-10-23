# Changelog

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-10-23

### Added
- `audit` 子命令：六维角色面板（档案/代码/活跃/协作/影响/成就），0–1100 分
- `next` 子命令：按缺口收益排序的任务清单
- 等级线 L1 种子 → L7 王者
- 双后端抓取：`gh` CLI 优先，`GITHUB_TOKEN` 兜底
- 离线快照：`--save-json` / `--from-json`，评分与网络彻底分离
- Markdown 面板输出 `--markdown`
- 徽章解析 `parse_achievements()`（HTML，无 API）
- 34 个单元测试，CI 覆盖 Python 3.9–3.13
