# CLAUDE.md - WebShare IP Quality Checker

## 项目概述
一个基于 FastMCP 的 WebShare 代理 IP 质量检测工具，支持自动更换 IP 并执行 `IP.Check.Place` 脚本进行详细检测。

## 运行与构建
- **运行 MCP 服务**: `python main.py`
- **安装依赖**: `pip install -r requirements.txt`
- **环境变量配置**:
  - `WEBSHARE_TOKEN`: WebShare API 令牌
  - `WEBSHARE_PLAN_ID`: WebShare 计划 ID
  - `WEBSHARE_SOCKS_USERNAME`: SOCKS5 代理用户名
  - `WEBSHARE_SOCKS_PASSWORD`: SOCKS5 代理密码
  - `HTTP_PROXY` / `HTTPS_PROXY`: (可选) 访问 WebShare API 的代理

## 代码规范
- **命名**: 使用 `snake_case` 命名函数和变量。
- **类型暗示**: 尽可能在函数定义中使用 Python 类型暗示 (Type Hinting)。
- **错误处理**: 使用 `try...except` 捕获网络请求和子进程执行中的异常。
- **工具定义**: 使用 `@mcp.tool` 装饰器定义对外暴露的 MCP 工具。

## 主要功能
- `replace_ip_and_check(asn: int)`: 更换一次 IP (可指定 ASN) 并执行质量检测脚本，返回 JSON 格式的详细报告。
- `check_webshare_connectivity()`: 检测与 WebShare API 的连通性。
- `webshare_replace_proxy(...)`: 处理 WebShare API 的 IP 更换逻辑。
