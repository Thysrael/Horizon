# Twitter / X Cookie 配置指南（Playwright 模式）

Horizon 支持两种 Twitter 抓取方式：

| 方式 | 成本 | 稳定性 | 适用场景 |
|------|------|--------|----------|
| **Apify** (默认) | 需订阅 ($49/月起) | ⭐⭐⭐ 高 | 生产环境、大量账号 |
| **Playwright + Cookie** (免费) | 免费 | ⭐⭐ 中 | 个人使用、少量账号 |

本文档介绍免费方案的配置方法。

---

## 1. 安装依赖

```bash
uv sync --extra twitter
uv run playwright install chromium
```

---

## 2. 获取 Cookie

### 方法一：浏览器扩展（推荐）

1. 用 Chrome/Edge/Firefox 登录 [x.com](https://x.com)
2. 安装扩展 **"Cookie-Editor"** 或 **"Get cookies.txt LOCALLY"**
3. 在 x.com 页面打开扩展，导出为 **JSON 格式**
4. 保存到 `data/x_cookies_1.json`

### 方法二：开发者工具

1. 登录 x.com 后按 `F12` 打开开发者工具
2. 切换到 **Application (应用)** → **Cookies** → `https://x.com`
3. 找到以下关键 Cookie（名称可能略有不同）：
   - `auth_token`
   - `ct0`
   - `twid`
4. 手动构建 JSON 数组：

```json
[
  {
    "name": "auth_token",
    "value": "你的auth_token值",
    "domain": ".x.com",
    "path": "/",
    "secure": true,
    "httpOnly": true
  },
  {
    "name": "ct0",
    "value": "你的ct0值",
    "domain": ".x.com",
    "path": "/",
    "secure": true,
    "httpOnly": false
  }
]
```

---

## 3. 配置文件

编辑 `data/config.json`：

```json
{
  "sources": {
    "twitter": {
      "enabled": true,
      "mode": "playwright",
      "users": ["karpathy", "ylecun"],
      "fetch_limit": 10,
      "cookie_dir": "data",
      "cookie_file_pattern": "x_cookies_*.json"
    }
  }
}
```

---

## 4. 多账号轮询（防封策略）

如果你有多个 X 账号，可以为每个账号导出 cookie，命名为：

```
data/x_cookies_1.json   # 账号A
data/x_cookies_2.json   # 账号B
data/x_cookies_3.json   # 账号C
```

Horizon 会自动**轮询使用**这些 cookie，当一个账号触发限流时切换到下一个，大幅提升稳定性。

---

## 5. 代理配置（可选）

如果在中国大陆或需要代理：

```bash
export https_proxy=http://127.0.0.1:7890
```

Playwright 会自动读取 `PROXY`、`https_proxy`、`http_proxy`、`all_proxy` 环境变量。

---

## 6. 注意事项

⚠️ **Cookie 有有效期**：通常 1-4 周，过期后需要重新导出  
⚠️ **不要提交 Cookie 文件**：已加入 `.gitignore`，请妥善保管  
⚠️ **账号安全**：建议使用**小号/备用号**，避免主账号风险  
⚠️ **抓取频率**：每个账号间隔 5-10 秒，避免触发平台限流

---

## 7. 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| "No cookie files found" | cookie 文件名不匹配 | 检查 `cookie_file_pattern` 和实际文件名 |
| "page shows login gate" | cookie 已过期 | 重新登录并导出最新 cookie |
| "no GraphQL data intercepted" | 页面结构变化或被限流 | 等待几分钟后重试，或增加 cookie 数量 |
| Playwright 未安装 | 依赖缺失 | 运行 `uv sync --extra twitter && uv run playwright install chromium` |
