## 运行说明
> claude 内执行
1. 修改mcp.json中的项目路径
2. 复制.env.example 为.env 并正确填写变量
3. 安装依赖 `pip install -r requirements.txt`
4. 在claude中使用
    > 需要指定你想要更换的asn，目前默认是6079 - RCN-as
    + case1: 单次更换并检查ip质量： "使用asn 6079, 更换当前ip，并分析ip质量"
    + case2: 重复执行检查ip质量：“使用asn 6079， 更换当前ip，如果ip质量不符合要求，则再次执行，最大执行50次”
    + case3: 自定义ip质量要求（未测试）： “使用asn 6079， 更换当前ip， ip风险要求小于中等及以下， ip类型可以是商业宽带， 如果不符合要求，则再次执行，最大执行50次”

## 命令行执行
除了在 Claude 内使用，你也可以直接使用 `find_ip.py` 脚本：
```bash
python find_ip.py --asn 6079 --max-tries 50 --min-low-risk 5 --max-commercial 2
```
- `--asn`: 指定 ASN 号码（默认: 6079）
- `--max-tries`: 最大尝试次数（默认: 50）
- `--min-low-risk`: 低风险 关键字数量
- `--max-commercial`: 商业 关键字数量
该脚本会自动循环更换 IP 并检测，直到找到符合高质量标准的 IP 为止（“低风险” >= min-low-risk 且 “商业” <= max-commercial）。找到后会保存到 `found_ip.json`。
