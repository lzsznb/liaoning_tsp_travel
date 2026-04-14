# tsp_api.py
import pandas as pd
import numpy as np
from itertools import permutations
import warnings
from flask import Flask, request, jsonify, send_file
import os
# 在tsp_api.py中添加
from flask_cors import CORS

warnings.filterwarnings('ignore')
# tsp_api.py 顶部导入后添加
import os
from flask import send_from_directory

# 配置静态文件目录（image文件夹路径）
# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'image')


app = Flask(__name__)
# 初始化CORS
CORS(app, resources=r'/*')
# 添加静态文件路由
@app.route('/image/<filename>')
def serve_image(filename):
    """托管image文件夹下的图片"""
    try:
        return send_from_directory(IMAGE_DIR, filename, as_attachment=False)
    except Exception as e:
        # 兜底返回默认图片（可选）
        return jsonify({"code": 404, "msg": "图片不存在"}), 404
# ========== 1. 初始化数据（复用原有逻辑） ==========
# 读取数据
df = pd.read_excel('highspeed_rail_fare.xlsx')

# 提取14个地级市名单
all_cities = list(set(df['from_city'].dropna().tolist() + df['to_city'].dropna().tolist()))
all_cities = [str(city).strip() for city in all_cities if str(city).strip() != '']
cities = all_cities[:14]

# 构建票价矩阵
n = len(cities)
max_fare = 10000
fare_matrix = np.full((n, n), max_fare, dtype=np.float64)
for i in range(n):
    fare_matrix[i, i] = 0.0

for _, row in df.iterrows():
    from_city = str(row['from_city']).strip()
    to_city = str(row['to_city']).strip()
    fare = float(row['fare_yuan']) if pd.notna(row['fare_yuan']) else max_fare
    if from_city in cities and to_city in cities:
        i = cities.index(from_city)
        j = cities.index(to_city)
        fare_matrix[i, j] = fare
        fare_matrix[j, i] = fare

# ========== 2. TSP算法（复用原有逻辑） ==========
def tsp_dynamic_programming(start_city, distance_matrix, cities):
    n = len(cities)
    start_idx = cities.index(start_city)
    mask_size = 1 << n
    dp = np.full((mask_size, n), float('inf'))
    prev = np.full((mask_size, n), -1)
    
    dp[1 << start_idx, start_idx] = 0.0
    
    for mask in range(mask_size):
        for u in range(n):
            if not (mask & (1 << u)):
                continue
            current_dist = dp[mask][u]
            if current_dist == float('inf'):
                continue
            for v in range(n):
                if mask & (1 << v):
                    continue
                new_mask = mask | (1 << v)
                new_dist = current_dist + distance_matrix[u][v]
                if new_dist < dp[new_mask][v]:
                    dp[new_mask][v] = new_dist
                    prev[new_mask][v] = u
    
    full_mask = (1 << n) - 1
    min_total_fare = float('inf')
    end_idx = -1
    
    for v in range(n):
        if v == start_idx:
            continue
        total_fare = dp[full_mask][v] + distance_matrix[v][start_idx]
        if total_fare < min_total_fare:
            min_total_fare = total_fare
            end_idx = v
    
    # 回溯路径
    path = []
    current_mask = full_mask
    current_idx = end_idx
    while current_idx != -1:
        path.append(current_idx)
        next_idx = prev[current_mask][current_idx]
        current_mask &= ~(1 << current_idx)
        current_idx = next_idx
    path.reverse()
    path.append(start_idx)
    path_cities = [cities[idx] for idx in path]
    
    # 生成分段明细
    segments = []
    total_verify = 0.0
    for i in range(len(path_cities)-1):
        city1 = path_cities[i]
        city2 = path_cities[i+1]
        idx1 = cities.index(city1)
        idx2 = cities.index(city2)
        segment_fare = fare_matrix[idx1][idx2]
        total_verify += segment_fare
        segments.append({
            "index": i+1,
            "from_city": city1,
            "to_city": city2,
            "fare": round(segment_fare, 1),
            "cumulative_fare": round(total_verify, 1)
        })
    
    return {
        "min_total_fare": round(min_total_fare, 1),
        "shortest_path": path_cities,
        "segments": segments,
        "city_list": cities
    }

# ========== 3. Flask接口 ==========
@app.route('/api/cities', methods=['GET'])
def get_cities():
    """获取可选城市列表"""
    return jsonify({
        "code": 200,
        "data": cities
    })

@app.route('/api/solve-tsp', methods=['POST'])
def solve_tsp():
    """求解TSP路径"""
    try:
        data = request.json
        start_city = data.get('start_city')
        
        if not start_city or start_city not in cities:
            return jsonify({
                "code": 400,
                "msg": "起点城市无效"
            })
        
        # 调用TSP算法
        result = tsp_dynamic_programming(start_city, fare_matrix, cities)
        
        return jsonify({
            "code": 200,
            "msg": "求解成功",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"求解失败：{str(e)}"
        })

@app.route('/api/report/<start_city>', methods=['GET'])
def get_report(start_city):
    """生成并返回markdown报告"""
    try:
        if start_city not in cities:
            return jsonify({"code": 400, "msg": "起点城市无效"})
        
        result = tsp_dynamic_programming(start_city, fare_matrix, cities)
        
        # 生成报告内容
        report = "# 辽宁省14地级市高铁TSP最短路径求解报告\n\n"
        report += "## 1. 项目概述\n"
        report += "- **求解目标**：从指定起点出发，游遍14个地级市后返回起点，寻找总票价最低的路径\n"
        report += "- **数据来源**：辽宁14地级市高铁票价表（无向图，A→B与B→A票价相同）\n"
        report += "- **求解算法**：动态规划法（保证全局最优解）\n\n"
        
        report += "## 2. 求解结果\n"
        report += f"- **起点城市**：{start_city}\n"
        report += f"- **最短总票价**：{result['min_total_fare']} 元\n"
        report += f"- **路径总段数**：{len(result['shortest_path'])-1} 段\n"
        path_str = " → ".join(result['shortest_path'])
        report += f"- **最短路径**：\n```\n{path_str}\n```\n\n"
        
        report += "## 3. 分段票价明细\n"
        report += "| 序号 | 出发城市 | 到达城市 | 票价（元） | 累计票价（元） |\n"
        report += "|------|----------|----------|------------|----------------|\n"
        for seg in result['segments']:
            report += f"| {seg['index']} | {seg['from_city']} | {seg['to_city']} | {seg['fare']} | {seg['cumulative_fare']} |\n"
        
        # 保存报告文件
        report_path = f"tsp_report_{start_city}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 返回文件
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"生成报告失败：{str(e)}"
        })
# ========== 新增：托管前端页面 ==========
from flask import send_from_directory

# 根路径路由：访问http://127.0.0.1:5000/ 打开index.html
@app.route('/')
def index():
    # 指向static文件夹下的index.html
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)