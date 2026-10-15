# star-radar

每周汇总 [@dengshu2](https://github.com/dengshu2) 关注的人在过去 7 天内 Star 了哪些仓库，供 AI 简报读取。

- GitHub Action（`.github/workflows/star-radar.yml`）每周一 07:07（Asia/Shanghai）运行，也可手动触发。
- 结果写入 [`stars.json`](stars.json) 并提交回 `main`。
- 下游匿名读取：`https://raw.githubusercontent.com/dengshu2/star-radar/main/stars.json`
- 只调用 GitHub 公开只读接口，使用 Action 自带的 `GITHUB_TOKEN`。
