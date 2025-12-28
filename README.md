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
