import os
import time
import requests
import json
import subprocess
from typing import Dict, Any, Optional
from fastmcp import FastMCP, Context

# 环境变量由 MCP (.mcp.json) 或系统环境提供
# 如果本地开发需要，可选加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 不是必需的，MCP 会通过 .mcp.json 注入环境变量

# 初始化 FastMCP
mcp = FastMCP("WebShare IP Quality 🚀")

# 1. 代理配置
HTTP_PROXY = os.getenv("HTTP_PROXY")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

def get_request_proxies():
    proxies = {}
    if HTTP_PROXY:
        proxies["http"] = HTTP_PROXY
    if HTTPS_PROXY:
        proxies["https"] = HTTPS_PROXY
    return proxies if proxies else None

# 2. WebShare 配置 (从环境变量读取)
WEBSHARE_TOKEN = os.getenv("WEBSHARE_TOKEN")
WEBSHARE_PLAN_ID = os.getenv("WEBSHARE_PLAN_ID")
WEBSHARE_SOCKS_USERNAME = os.getenv("WEBSHARE_SOCKS_USERNAME")
WEBSHARE_SOCKS_PASSWORD = os.getenv("WEBSHARE_SOCKS_PASSWORD")

def check_webshare_connectivity() -> tuple[bool, str]:
    """
    检测 WebShare 连接性，5秒超时。
    Returns:
        (is_connected, error_message)
    """
    try:
        proxies = get_request_proxies()
        response = requests.get(
            "https://dashboard.webshare.io",
            proxies=proxies,
            timeout=5
        )
        if response.status_code == 200:
            return True, ""
        return False, f"WebShare returned status code: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "连接 WebShare 超时，请检查网络或设置/更换 proxy"
    except requests.exceptions.ProxyError:
        return False, "代理连接失败，请检查 HTTP_PROXY/HTTPS_PROXY 设置"
    except requests.exceptions.ConnectionError:
        return False, "无法连接 WebShare，请检查网络或设置/更换 proxy"
    except Exception as e:
        return False, f"网络连接错误: {str(e)}"

def webshare_replace_proxy(
    token: str,
    plan_id: str,
    socks_username: str,
    socks_password: str,
    asn: int = 6079,
    wait_seconds: int = 5
) -> Dict[str, Any] | None:
    headers = {
        "authorization": f"Token {token}",
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0"
    }

    current_proxies = get_request_proxies()
    cookies = {"ssotoken": token}

    def get_latest_proxy():
        url = f"https://proxy.webshare.io/api/v2/proxy/list/replaced/?page=1&page_size=1&plan_id={plan_id}"
        try:
            response = requests.get(url, headers=headers, cookies=cookies, proxies=current_proxies, timeout=30)
            if response.status_code == 200:
                results = response.json().get("results")
                if results:
                    return results[0].get("replaced_with"), results[0].get("replaced_with_port")
        except Exception:
            pass
        return None, None

    def replace(ip):
        url = f"https://proxy.webshare.io/api/v2/proxy/replace/?plan_id={plan_id}"
        data = {
            "to_replace": {"type": "ip_address", "ip_addresses": [ip]},
            "replace_with": [{"type": "asn", "asn_numbers": [asn]}],
            "dry_run": False
        }
        try:
            response = requests.post(url, headers=headers, cookies=cookies, json=data, proxies=current_proxies, timeout=30)
            return response.status_code in [200, 201]
        except Exception:
            return False

    current_ip, _ = get_latest_proxy()
    if not current_ip:
        return None

    if not replace(current_ip):
        return None

    time.sleep(wait_seconds)

    new_ip, new_port = None, None
    for _ in range(5):
        new_ip, new_port = get_latest_proxy()
        if new_ip and new_ip != current_ip:
            break
        time.sleep(3)

    if not new_ip or new_ip == current_ip:
        return None

    socks_url = f"socks5://{socks_username}:{socks_password}@{new_ip}:{new_port}"
    socks_cmd = f"bash <(curl -Ls IP.Check.Place) -x {socks_url}"

    return {
        "cmd": socks_cmd,
        "ip": new_ip,
        "port": new_port,
        "socks_url": socks_url
    }

@mcp.tool
async def replace_ip_and_check(
    asn: int = 6079,
    ctx: Context = None
) -> str:
    """
    更换一次 IP 并执行质量检测,返回原始检测报告。

    Args:
        asn: 更换 IP 时指定的 ASN (默认 6079)

    Returns:
        JSON 格式结果,包含:
        - status: 执行状态 (success/failed)
        - ip: 新的 IP 地址
        - socks_url: SOCKS5 代理 URL
        - report: 完整的质量检测报告文本
    """
    total_steps = 4

    # Step 1: 前置连接检测
    if ctx:
        await ctx.report_progress(progress=1, total=total_steps, message="正在检测 WebShare 连接...")

    is_connected, conn_error = check_webshare_connectivity()
    if not is_connected:
        return json.dumps({
            "status": "failed",
            "step": "connectivity_check",
            "message": conn_error
        }, indent=2)

    # Step 2: 验证环境变量
    if ctx:
        await ctx.report_progress(progress=2, total=total_steps, message="正在验证配置...")

    token = os.getenv("WEBSHARE_TOKEN")
    plan_id = os.getenv("WEBSHARE_PLAN_ID")
    socks_username = os.getenv("WEBSHARE_SOCKS_USERNAME")
    socks_password = os.getenv("WEBSHARE_SOCKS_PASSWORD")

    if not all([token, plan_id, socks_username, socks_password]):
        missing = []
        if not token: missing.append("WEBSHARE_TOKEN")
        if not plan_id: missing.append("WEBSHARE_PLAN_ID")
        if not socks_username: missing.append("WEBSHARE_SOCKS_USERNAME")
        if not socks_password: missing.append("WEBSHARE_SOCKS_PASSWORD")

        env_keys = [k for k in os.environ.keys() if 'WEBSHARE' in k or 'LLM' in k or 'PROXY' in k]
        return json.dumps({
            "status": "failed",
            "step": "config_validation",
            "message": f"Missing WebShare configuration: {missing}",
            "available_env_keys": env_keys
        }, indent=2)

    # Step 3: 更换 IP
    if ctx:
        await ctx.report_progress(progress=3, total=total_steps, message=f"正在更换 IP (ASN: {asn})...")

    res = webshare_replace_proxy(token, plan_id, socks_username, socks_password, asn=asn)
    if not res:
        return json.dumps({
            "status": "failed",
            "step": "ip_replacement",
            "message": "Failed to replace WebShare proxy IP."
        }, indent=2)

    ip = res["ip"]
    cmd = res["cmd"]

    # Step 4: 执行质量检测
    if ctx:
        await ctx.report_progress(progress=4, total=total_steps, message=f"正在执行 IP 质量检测 ({ip})...")

    try:
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash', timeout=300)
        report_text = process.stdout
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "step": "quality_check",
            "ip": ip,
            "message": f"Quality check command failed: {str(e)}"
        }, indent=2)

    return json.dumps({
        "status": "success",
        "ip": ip,
        "socks_url": res["socks_url"],
        "report": report_text
    }, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
