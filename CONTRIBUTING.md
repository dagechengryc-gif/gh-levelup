# 参与贡献

## 开发环境

```bash
git clone https://github.com/dagechengryc-gif/gh-levelup
cd gh-levelup
python3 -m pip install -e ".[dev]"
python3 -m unittest discover -s tests -t . -v
```

要求 Python 3.9+，不引入运行时依赖。

## 提交前自查

- [ ] `python3 -m unittest discover -s tests -t .` 全绿
- [ ] 新增评分项同时更新 `docs/scoring.md` 与 `README.md` 的分档表
- [ ] 新增纯函数必须带单测；网络调用不得进入 `scoring.py`
- [ ] 中文文案用简体，代码标识符用英文

## 分支与提交

- 分支：`feat/<短描述>`、`fix/<短描述>`
- 提交：`feat: ...` / `fix: ...` / `docs: ...` / `test: ...`（Conventional Commits）
- 一个 PR 只做一件事；改了输出格式请附前后截图或文本块

## 报 bug 请带上

```
gh-levelup --version
python3 -V
操作系统
gh-levelup audit -u <账号> --save-json snap.json  # 敏感字段可删
```
