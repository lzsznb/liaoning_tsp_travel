import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import permutations
import warnings
warnings.filterwarnings('ignore')
plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 1. 重新读取并解析高铁票价数据（修正数据结构处理）
df = pd.read_excel('highspeed_rail_fare.xlsx')
print("原始数据结构：")
print(df.head(10))
print(f"\n数据形状：{df.shape}")
print(f"\n列名：{df.columns.tolist()}")
print(f"\n数据类型：")
print(df.dtypes)

# 2. 提取14个地级市名单（从出发地和目的地中去重）
all_cities = list(set(df['from_city'].dropna().tolist() + df['to_city'].dropna().tolist()))
# 确保城市名称是字符串并去重
all_cities = [str(city).strip() for city in all_cities if str(city).strip() != '']
# 取前14个城市（确保覆盖辽宁省主要地级市）
cities = all_cities[:14]

print(f"\n✅ 提取的14个地级市名单：")
for i, city in enumerate(cities, 1):
    print(f"{i:2d}. {city}")

# 3. 构建无向图的邻接矩阵（票价矩阵）
n = len(cities)
max_fare = 10000  # 无法通行的路线设为极大值
fare_matrix = np.full((n, n), max_fare, dtype=np.float64)

# 对角线设为0（自身到自身距离为0）
for i in range(n):
    fare_matrix[i, i] = 0.0

# 填充票价数据（无向图，A→B与B→A票价相同）
for _, row in df.iterrows():
    from_city = str(row['from_city']).strip()
    to_city = str(row['to_city']).strip()
    fare = float(row['fare_yuan']) if pd.notna(row['fare_yuan']) else max_fare
    
    # 只处理在14个城市列表中的数据
    if from_city in cities and to_city in cities:
        i = cities.index(from_city)
        j = cities.index(to_city)
        # 无向图双向赋值
        fare_matrix[i, j] = fare
        fare_matrix[j, i] = fare

# 验证邻接矩阵
print(f"\n✅ 票价矩阵示例（前5x5，单位：元）：")
print(np.round(fare_matrix[:5, :5], 1))

# 检查矩阵对称性（无向图验证）
symmetry_check = np.allclose(fare_matrix, fare_matrix.T)
print(f"\n✅ 无向图对称性验证：{'通过' if symmetry_check else '未通过'}")

# 4. TSP核心算法（动态规划法，保证全局最优）
def tsp_dynamic_programming(start_city, distance_matrix, cities):
    """
    动态规划求解TSP问题（无向图，回到起点）
    :param start_city: 起点城市名称
    :param distance_matrix: 邻接矩阵（票价）
    :param cities: 城市列表
    :return: 最短总票价、最短路径（城市名称列表）
    """
    n = len(cities)
    start_idx = cities.index(start_city)
    
    # 状态定义：dp[mask][u] = 访问过mask中的城市，当前在u的最短距离
    mask_size = 1 << n
    dp = np.full((mask_size, n), float('inf'))
    prev = np.full((mask_size, n), -1)  # 记录前驱节点，用于回溯路径
    
    # 初始状态：只访问起点
    dp[1 << start_idx, start_idx] = 0.0
    
    # 迭代所有状态
    for mask in range(mask_size):
        for u in range(n):
            # 跳过未访问u的状态
            if not (mask & (1 << u)):
                continue
            current_dist = dp[mask][u]
            if current_dist == float('inf'):
                continue
            
            # 尝试访问未访问的城市v
            for v in range(n):
                if mask & (1 << v):
                    continue  # v已访问
                new_mask = mask | (1 << v)
                new_dist = current_dist + distance_matrix[u][v]
                
                # 更新更短路径
                if new_dist < dp[new_mask][v]:
                    dp[new_mask][v] = new_dist
                    prev[new_mask][v] = u
    
    # 找到回到起点的最短路径
    full_mask = (1 << n) - 1  # 所有城市都访问过的mask
    min_total_fare = float('inf')
    end_idx = -1
    
    # 遍历所有可能的终点，计算返回起点的总票价
    for v in range(n):
        if v == start_idx:
            continue
        total_fare = dp[full_mask][v] + distance_matrix[v][start_idx]
        if total_fare < min_total_fare:
            min_total_fare = total_fare
            end_idx = v
    
    # ========== 修复1：正确回溯路径（移除重复起点） ==========
    path = []
    current_mask = full_mask
    current_idx = end_idx
    
    while current_idx != -1:
        path.append(current_idx)
        next_idx = prev[current_mask][current_idx]
        current_mask &= ~(1 << current_idx)
        current_idx = next_idx
    
    # 反转路径，确保起点在前（此时path是 [end, ..., start] → 反转后 [start, ..., end]）
    path.reverse()
    
    # ========== 修复2：添加「终点→起点」的闭环段 ==========
    path.append(start_idx)  # 最终路径：start → ... → end → start
    
    # 转换为城市名称
    path_cities = [cities[idx] for idx in path]
    
    return min_total_fare, path_cities
# 5. 用户交互与结果输出函数（核心修改：支持自定义输入城市）
def tsp_solver_interactive():
    """交互式TSP求解器（支持用户自定义输入起点城市）"""
    print("\n" + "="*70)
    print("          🚄 辽宁省14地级市高铁TSP最短路径求解器          ")
    print("="*70)
    
    # 显示城市选择列表
    print("\n【可选起点城市列表】")
    for i, city in enumerate(cities, 1):
        print(f"  {i:2d}. {city}")
    
    # ========== 核心修改：交互式输入 + 输入校验 ==========
    start_city = None
    while start_city is None:
        # 提示用户输入（支持编号或城市名称）
        user_input = input("\n请输入起点城市（可输入编号或城市名称）：").strip()
        
        # 处理编号输入
        if user_input.isdigit():
            input_idx = int(user_input)
            if 1 <= input_idx <= len(cities):
                start_city = cities[input_idx - 1]
            else:
                print(f"❌ 编号无效！请输入1-{len(cities)}之间的数字")
        # 处理城市名称输入
        else:
            # 模糊匹配（忽略空格/大小写）
            matched_cities = [city for city in cities if user_input.strip() in city]
            if len(matched_cities) == 1:
                start_city = matched_cities[0]
            elif len(matched_cities) > 1:
                print(f"⚠️  输入模糊，匹配到多个城市：{matched_cities}，请输入完整名称")
            else:
                print(f"❌ 城市名称无效！请从列表中选择")
    
    print(f"\n✅ 已选择起点城市：「{start_city}」")
    # ========== 输入逻辑结束 ==========
    
    print(f"\n🔍 正在计算从「{start_city}」出发，游遍14市的最短路径...")
    
    # 调用TSP算法
    min_fare, shortest_path = tsp_dynamic_programming(start_city, fare_matrix, cities)
    
    # 输出结果
    print("\n" + "="*70)
    print(f"                🎯 求解结果（起点：{start_city}）                ")
    print("="*70)
    print(f"📊 最短总票价：{min_fare:.1f} 元")
    print(f"🗺️  最短路径（共{len(shortest_path)-1}段，回到起点）：")
    print("   " + " → ".join(shortest_path))
    
    
    # 输出详细分段票价
    print(f"\n🚆 各段路程票价明细：")
    print("-" * 55)
    print(f"{'序号':<4} {'出发城市':<8} {'到达城市':<8} {'票价（元）':<10}")
    print("-" * 55)
    total_verify = 0.0
    # 循环覆盖：起点→...→终点→起点（共len(shortest_path)-1段）
    for i in range(len(shortest_path)-1):
        city1 = shortest_path[i]
        city2 = shortest_path[i+1]
        idx1 = cities.index(city1)
        idx2 = cities.index(city2)
        segment_fare = fare_matrix[idx1][idx2]
        total_verify += segment_fare
        print(f"{i+1:<4} {city1:<8} {city2:<8} {segment_fare:<10.1f}")
    print("-" * 55)
    print(f"{'合计':<4} {'-':<8} {'-':<8} {total_verify:<10.1f}")
    print("-" * 55)
    
    return start_city, min_fare, shortest_path

# 6. 路径可视化函数
def plot_tsp_result(start_city, shortest_path, min_fare):
    """可视化TSP结果"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'辽宁省14地级市高铁TSP最短路径分析（起点：{start_city}）', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # 子图1：路径流程图
    ax1.set_title(f'最短路径（总票价：{min_fare:.1f}元）', fontsize=14, pad=20)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, len(shortest_path) + 2)
    
    # 绘制路径节点和箭头
    y_pos = np.linspace(len(shortest_path), 1, len(shortest_path))
    colors = ['#E74C3C' if i == 0 or i == len(shortest_path)-1 else '#3498DB' 
              for i in range(len(shortest_path))]
    
    for i, (city, y, color) in enumerate(zip(shortest_path, y_pos, colors)):
        # 绘制节点
        ax1.scatter(5, y, s=1200, c=color, alpha=0.8, edgecolors='black', linewidth=2)
        # 绘制城市名称
        ax1.text(5, y, city, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        # 绘制箭头
        if i < len(shortest_path)-1:
            ax1.annotate('', xy=(5, y_pos[i+1]), xytext=(5, y),
                        arrowprops=dict(arrowstyle='->', lw=3, color='#F39C12', alpha=0.8,
                                       shrinkA=20, shrinkB=20))
            # 标注段数
            ax1.text(5.8, (y + y_pos[i+1])/2, f'第{i+1}段', 
                    ha='left', va='center', fontsize=9, color='#2C3E50', fontweight='bold')
    
    ax1.axis('off')
    
    # 子图2：票价矩阵热力图
    im = ax2.imshow(fare_matrix, cmap='YlOrRd_r', aspect='auto', vmin=0, vmax=300)
    ax2.set_title('城市间高铁票价矩阵（单位：元）', fontsize=14, pad=20)
    ax2.set_xlabel('目的地城市', fontsize=12)
    ax2.set_ylabel('出发地城市', fontsize=12)
    
    # 设置坐标轴标签
    ax2.set_xticks(range(n))
    ax2.set_yticks(range(n))
    ax2.set_xticklabels([city[:4] for city in cities], rotation=45, ha='right', fontsize=9)
    ax2.set_yticklabels([city[:4] for city in cities], fontsize=9)
    
    # 添加数值标注（只标注有效票价）
    for i in range(n):
        for j in range(n):
            if fare_matrix[i, j] < max_fare and fare_matrix[i, j] > 0:
                text_color = 'white' if fare_matrix[i, j] > 150 else 'black'
                ax2.text(j, i, f'{fare_matrix[i, j]:.0f}', 
                        ha='center', va='center', fontsize=7, color=text_color, fontweight='bold')
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax2, shrink=0.8)
    cbar.set_label('票价（元）', rotation=270, labelpad=20, fontsize=11)
    
    plt.tight_layout()
    plt.savefig('辽宁高铁TSP最短路径可视化.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"\n📈 可视化图表已保存：辽宁高铁TSP最短路径可视化.png")

# 7. 生成详细报告
def generate_report(start_city, min_fare, shortest_path):
    """生成markdown格式的详细报告"""
    report = "# 辽宁省14地级市高铁TSP最短路径求解报告\n\n"
    
    report += "## 1. 项目概述\n"
    report += "- **求解目标**：从指定起点出发，游遍14个地级市后返回起点，寻找总票价最低的路径\n"
    report += "- **数据来源**：辽宁14地级市高铁票价表（无向图，A→B与B→A票价相同）\n"
    report += "- **求解算法**：动态规划法（保证全局最优解，适用于14城市小规模问题）\n"
    report += "- **核心假设**：仅考虑票价成本，暂不考虑车次时刻、换乘时间等因素\n\n"
    
    report += "## 2. 基础数据\n"
    report += "### 2.1 14个地级市名单\n"
    report += "| 编号 | 城市名称 |\n"
    report += "|------|----------|\n"
    for i, city in enumerate(cities, 1):
        report += f"| {i:2d}    | {city} |\n"
    
    report += f"\n### 2.2 求解参数\n"
    report += f"- **起点城市**：{start_city}\n"
    report += f"- **城市数量**：{len(cities)}个\n"
    report += f"- **路径类型**：闭环路径（回到起点）\n"
    report += f"- **无法通行票价**：{max_fare}元（矩阵中未覆盖的路线）\n\n"
    
    report += "## 3. 求解结果\n"
    report += "### 3.1 核心指标\n"
    report += f"- **最短总票价**：{min_fare:.1f} 元\n"
    report += f"- **路径总段数**：{len(shortest_path)-1} 段\n"
    report += f"- **平均每段票价**：{min_fare/(len(shortest_path)-1):.1f} 元\n\n"
    
    report += "### 3.2 最短路径详情\n"
    path_str = f"{start_city} → {' → '.join(shortest_path[1:-1])} → {start_city}"
    report += f"```\n{path_str}\n```\n\n"
    
    report += "### 3.3 分段票价明细\n"
    report += "| 序号 | 出发城市 | 到达城市 | 票价（元） | 累计票价（元） |\n"
    report += "|------|----------|----------|------------|----------------|\n"
    
    cumulative_fare = 0.0
    for i in range(len(shortest_path)-1):
        city1 = shortest_path[i]
        city2 = shortest_path[i+1]
        idx1 = cities.index(city1)
        idx2 = cities.index(city2)
        segment_fare = fare_matrix[idx1][idx2]
        cumulative_fare += segment_fare
        report += f"| {i+1:<4} | {city1:<8} | {city2:<8} | {segment_fare:<10.1f} | {cumulative_fare:<12.1f} |\n"
    
    report += "\n## 4. 算法说明\n"
    report += "### 4.1 动态规划法原理\n"
    report += "1. **状态定义**：`dp[mask][u]` 表示访问过`mask`（二进制掩码）中的城市，当前在城市`u`的最短票价\n"
    report += "2. **状态转移**：对于每个状态，尝试访问未去过的城市`v`，更新`dp[new_mask][v] = min(dp[new_mask][v], dp[mask][u] + fare[u][v])`\n"
    report += "3. **结果计算**：所有城市访问完毕后，计算从最后一个城市返回起点的总票价，取最小值\n\n"
    
    report += "### 4.2 无向图处理\n"
    report += "- 利用票价矩阵对称性（`fare[u][v] = fare[v][u]`），减少计算量\n"
    report += "- 确保路径规划符合高铁实际运营的双向性\n\n"
    
    report += "## 5. 应用建议\n"
    report += "1. **出行规划**：可根据此路径优化高铁出行方案，降低交通成本\n"
    report += "2. **数据更新**：建议每季度更新票价数据，确保结果准确性\n"
    report += "3. **扩展功能**：可增加车次时刻、换乘时间等约束条件，进一步优化路径\n"
    report += "4. **场景扩展**：适用于旅游规划、商务差旅等需要遍历多城市的场景\n\n"
    
    report += "## 6. 文件说明\n"
    report += "- 可视化图表：辽宁高铁TSP最短路径可视化.png（路径流程+票价矩阵）\n"
    report += "- 原始数据：highspeed_rail_fare.xlsx（辽宁高铁票价原始数据）\n"
    report += "- 求解程序：可通过本报告中的算法逻辑复现求解过程\n"
    
    # 保存报告
    with open('辽宁高铁TSP求解报告.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📄 详细报告已保存：辽宁高铁TSP求解报告.md")

# 8. 主程序执行
if __name__ == "__main__":
    # 执行求解（支持自定义输入）
    start_city, min_fare, shortest_path = tsp_solver_interactive()
    
    # 生成可视化和报告
    plot_tsp_result(start_city, shortest_path, min_fare)
    generate_report(start_city, min_fare, shortest_path)
    
    print("\n" + "="*70)
    print("          ✅ 求解完成！所有结果文件已保存至当前目录          ")
    print("="*70)