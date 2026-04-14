# 辽宁省14地级市高铁TSP最短路径求解

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

基于动态规划算法求解辽宁省14个地级市的高铁票价最低环游路径（Traveling Salesman Problem, TSP）。

## 项目背景

TSP问题是组合优化领域的经典问题，要求找到访问所有城市并返回起点的最短路径。本项目以辽宁省14个地级市之间的高铁票价为数据，求解总票价最低的旅行路线。

## 功能特性

- ✅ 动态规划算法，保证全局最优解
- ✅ 支持任意城市作为起点
- ✅ Web可视化界面，交互友好
- ✅ 命令行版本，支持可视化图表输出
- ✅ 支持生成详细求解报告

## 环境要求

- Python 3.8+
- Windows / Linux / Mac

## 项目结构

```
├── tsp_api.py              # Flask Web API服务
├── tsp_simple.py           # 命令行交互版本
├── highspeed_rail_fare.xlsx # 高铁票价原始数据
├── data/
│   ├── highspeed_rail_fare.xlsx
│   └── highspeed_rail_fare.csv
├── image/                  # 城市图片目录
├── static/
│   └── index.html         # Web前端页面
├── 辽宁高铁TSP求解报告.md  # 求解报告示例
└── README.md
```

## 快速开始

### 方式一：Web界面（推荐）

```bash
python tsp_api.py
```

服务启动后，打开浏览器访问：http://127.0.0.1:5000

### 方式二：命令行版本

```bash
python tsp_simple.py
```

按提示输入起点城市编号或名称即可。

## API接口

服务地址：`http://127.0.0.1:5000`

| 接口                         | 方法 | 说明                        |
| ---------------------------- | ---- | --------------------------- |
| `/`                        | GET  | Web界面                     |
| `/api/cities`              | GET  | 获取城市列表                |
| `/api/solve-tsp`           | POST | 求解TSP（参数：start_city） |
| `/api/report/<start_city>` | GET  | 下载求解报告                |
| `/image/<filename>`        | GET  | 获取城市图片                |

### 请求示例

```bash
curl -X POST http://127.0.0.1:5000/api/solve-tsp \
  -H "Content-Type: application/json" \
  -d '{"start_city": "沈阳"}'
```

### 响应示例

```json
{
  "code": 200,
  "msg": "求解成功",
  "data": {
    "min_total_fare": 999.5,
    "shortest_path": ["沈阳", "抚顺", "铁岭", "...", "沈阳"],
    "segments": [
      {"index": 1, "from_city": "沈阳", "to_city": "抚顺", "fare": 25.0, "cumulative_fare": 25.0},
      ...
    ],
    "city_list": ["沈阳", "大连", "鞍山", ...]
  }
}
```

## 算法说明

### 动态规划法

本项目采用动态规划（DP）算法求解TSP问题，时间复杂度 O(n² × 2ⁿ)。

状态定义：

- `dp[mask][u]`：访问过集合 `mask` 中的城市，当前位于城市 `u` 的最低票价

状态转移：

```
dp[new_mask][v] = min(dp[new_mask][v], dp[mask][u] + fare[u][v])
```

其中 `new_mask = mask | (1 << v)`，表示将城市 `v` 加入已访问集合。

### 无向图处理

高铁票价矩阵为对称矩阵，满足 `fare[i][j] = fare[j][i]`。

## 数据说明

### 城市列表

辽宁省14个地级市：沈阳、大连、鞍山、抚顺、本溪、丹东、锦州、营口、阜新、辽阳、盘锦、铁岭、朝阳、葫芦岛

### 票价矩阵

票价数据存储在 `highspeed_rail_fare.xlsx`，包含以下字段：

- `from_city`：出发城市
- `to_city`：到达城市
- `fare_yuan`：票价（元）

## 示例输出

以沈阳为起点的求解结果：

- **最短总票价**：999.5 元
- **最短路径**：沈阳 → 抚顺 → 铁岭 → ... → 沈阳

详细分段票价见 `辽宁高铁TSP求解报告.md`

## 依赖库

```
flask>=2.0
flask-cors
pandas
numpy
matplotlib
openpyxl
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
