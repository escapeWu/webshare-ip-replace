import os
import time
import requests
import json
import asyncio
import re
import argparse
import subprocess
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Copying logic from main.py to make find_ip.py self-contained
HTTP_PROXY = os.getenv("HTTP_PROXY")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

def get_request_proxies():
    proxies = {}
    if HTTP_PROXY:
        proxies["http"] = HTTP_PROXY
    if HTTPS_PROXY:
        proxies["https"] = HTTPS_PROXY
    return proxies if proxies else None

def check_webshare_connectivity() -> tuple[bool, str]:
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
    except Exception as e:
        return False, f"Connectivity error: {str(e)}"

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

async def replace_ip_and_check_logic(asn: int = 6079) -> str:
    is_connected, conn_error = check_webshare_connectivity()
    if not is_connected:
        return json.dumps({"status": "failed", "message": conn_error})

    token = os.getenv("WEBSHARE_TOKEN")
    plan_id = os.getenv("WEBSHARE_PLAN_ID")
    socks_username = os.getenv("WEBSHARE_SOCKS_USERNAME")
    socks_password = os.getenv("WEBSHARE_SOCKS_PASSWORD")

    if not all([token, plan_id, socks_username, socks_password]):
        return json.dumps({"status": "failed", "message": "Missing environment variables"})

    res = webshare_replace_proxy(token, plan_id, socks_username, socks_password, asn=asn)
    if not res:
        return json.dumps({"status": "failed", "message": "Failed to replace IP"})

    ip = res["ip"]
    cmd = res["cmd"]

    try:
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash', timeout=300)
        report_text = process.stdout
    except Exception as e:
        return json.dumps({"status": "failed", "message": str(e)})

    return json.dumps({
        "status": "success",
        "ip": ip,
        "socks_url": res["socks_url"],
        "report": report_text
    }, ensure_ascii=False)

def check_quality(report: str) -> tuple[bool, int, int]:
    # 移除 ANSI 转义序列以便正确匹配
    clean_report = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', report)

    low_risk_count = len(re.findall(r"低风险", clean_report))
    business_count = len(re.findall(r"商业", clean_report))

    is_good = low_risk_count >= 6 and business_count <= 2
    return is_good, low_risk_count, business_count

def save_report(ip: str, report: str):
    filename = f"{ip}-report.log"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {filename}")

async def main():
    parser = argparse.ArgumentParser(description="Find High Quality IP")
    parser.add_argument("--asn", type=int, default=6079, help="ASN number (default: 6079)")
    parser.add_argument("--max-tries", type=int, default=50, help="Maximum number of tries (default: 50)")
    args = parser.parse_args()

    asn = args.asn
    max_tries = args.max_tries

    # 1. Removed Pre-check test-report.log
    print(f"Starting search for high quality IP. ASN: {asn}, Max Tries: {max_tries}")

    for i in range(1, max_tries + 1):
        print(f"\n[Attempt {i}/{max_tries}] Replacing IP and checking quality...")

        try:
            result_json = await replace_ip_and_check_logic(asn=asn)
            result = json.loads(result_json)
        except Exception as e:
            print(f"Unexpected error: {e}")
            continue

        if result.get("status") != "success":
            print(f"Failed: {result.get('message')}")
            continue

        ip = result.get("ip")
        report = result.get("report", "")
        socks_url = result.get("socks_url")

        # Save report for every attempt
        save_report(ip, report)

        is_good, low_risk, business = check_quality(report)
        print(f"IP: {ip}")
        print(f"Counts -> 低风险: {low_risk}, 商业: {business}")

        if is_good:
            print(f"\n✨ SUCCESS! High quality IP found: {ip}")
            print(f"SOCKS5 URL: {socks_url}")
            print(f"Final Counts -> 低风险: {low_risk}, 商业: {business}")

            with open("found_ip.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            return

        print("Criteria not met. Continuing...")

    print(f"\n❌ Finished {max_tries} attempts without finding a suitable IP.")

if __name__ == "__main__":
    asyncio.run(main())
