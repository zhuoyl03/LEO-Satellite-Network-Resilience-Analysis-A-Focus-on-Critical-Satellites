# 项目代码逻辑记录

这个文件用于记录 `project/` 目录里重要代码逻辑。之后每次补充关键代码、实验假设、数据结构或指标定义，都应该在这里追加说明，避免代码越改越难追踪。

## 维护约定

- 新增实验层、核心数据结构、指标或路径约定时，必须在本文档新增一节。
- 写清楚“输入是什么、如何计算、输出是什么、哪些是假设而不是真实系统行为”。
- 如果只是小的格式化、注释或 bug fix，可以不更新；如果会影响实验含义，需要更新。
- 本文件记录的是研究代码逻辑，不替代论文文字，也不声称模拟真实 Starlink/Kuiper 流量。

## 现有主线逻辑概览

### Baseline resilience pipeline

主入口是 `project/satellites_analysis.py`。

核心流程：

1. 从 Hypatia 生成的卫星网络状态中读取卫星、地面站和链路数据。
2. 使用 `project/satellite_networks/construct_graph.py` 构建带距离权重的 NetworkX 图。
3. 使用 `project/satellite_networks/gen_path.py` 为地面站对计算最短路径。
4. 使用 `project/satgen_analysis/analyze_rtt_with_graph.py` 基于路径长度计算 RTT 相关统计。
5. 删除关键卫星的实验通过 `delete_50`、`delete_100` 等目录区分。

图数据格式：

- graph pickle 是 NetworkX `Graph`。
- 节点 ID 中，卫星节点通常是 `0 ... satellite_count - 1`。
- 地面站节点通常从 `satellite_count` 开始，即 `satellite_count + ground_station_id`。
- 边的 `weight` 表示链路距离，单位是米。

路径数据格式：

- `all_paths.pkl` 是一个字典。
- 外层 key 是 `time_ns`。
- 内层 key 是 `(src_ground_station_id, dst_ground_station_id)`。
- value 是节点路径列表，或者 `None` 表示不可达。

### Result directory

绘图脚本和生成结果已经分离：

- `project/result/plot_scripts/`：绘图脚本源码。
- `project/result/generated/`：本地生成图片、PDF、视频等结果，不提交到 git。

## 2026-06-06: Risk Displacement First Step

### 目标

新增第一阶段分析层：

固定 top-100 population city ground stations  
→ 生成多个可能的 traffic matrix  
→ 在代表性图快照上按不同 routing policy 路由 flow  
→ 根据 flow path 叠加计算 edge load  
→ 根据 edge load 计算 link stress  
→ 计算基础传播时延和 congestion-adjusted latency  
→ 输出 per-scenario / per-policy 指标

这个阶段不做：

- ML / RL / GNN
- agent
- ns-3 validation
- 真实 Starlink/Kuiper 流量建模
- 新的完整 routing protocol
- critical satellite removal impact

### 新增文件

包目录：

```text
project/satgen_analysis/risk_displacement/
```

模块：

- `scenarios.py`：ground station 和 flow 数据结构，以及 ground station 文件读取。
- `traffic_models.py`：traffic scenario / traffic matrix 生成。
- `routing_policies.py`：代表性 routing policy。
- `link_stress.py`：edge load 和 link stress 计算。
- `metrics.py`：latency 和聚合指标。
- `run_first_step.py`：第一阶段 orchestration。

入口脚本：

- 仓库根目录：`run_risk_displacement_first_step.py`
- project 内部：`project/run_risk_displacement_first_step.py`

推荐从仓库根目录运行：

```bash
conda run -n hypatia python run_risk_displacement_first_step.py \
  --traffic_models random_permutation_equal population_weighted gravity_model regional_hotspot \
  --num_seeds 3 \
  --num_pairs 50 \
  --reciprocal \
  --routing_policies shortest_path stress_aware_two_pass k_shortest_load_balancing \
  --link_capacity 10.0 \
  --alpha 2.0 \
  --beta 0.5 \
  --k_paths 3
```

### Ground station 读取逻辑

使用固定的 top-100 city ground station 文件：

```text
paper/satellite_networks_state/input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt
```

当前文件格式类似：

```text
0,Tokyo,35.6895,139.69171,0
1,Delhi,28.66667,77.21667,0
```

当前文件没有人口字段。因此：

- city name 使用第二列。
- latitude / longitude 使用第三、第四列。
- population 缺失时 fallback 为 uniform population weight，也就是 `1.0`。
- 代码会打印 warning。
- 后续如果 ground station 文件加入 population 字段，`scenarios.py` 已预留 `population` 字段。

### Flow 数据结构

一个 flow 代表某个 traffic scenario 下的一条 offered-load demand。

字段：

- `scenario_name`
- `traffic_model`
- `seed`
- `flow_id`
- `src_gs`
- `dst_gs`
- `src_city`
- `dst_city`
- `demand_weight`

注意：

- `demand_weight` 是 offered-load proxy，不是 Mbps。
- 本阶段不声称模拟真实用户流量。
- 如果使用 `--reciprocal`，每个 pair 会生成两个方向的 flow，两个方向使用相同 `demand_weight`。

### Traffic scenario 和 demand_weight 定义

所有 traffic model 都只在固定 top-100 ground stations 之间生成需求，不改变 ground station set。

#### 1. `random_permutation_equal`

逻辑：

1. 用 deterministic seed 对固定 ground station 列表随机 shuffle。
2. 每两个 ground station 配成一对。
3. 重复直到达到 `num_pairs`。
4. 每个 pair 的需求相同。

权重：

```text
demand_weight = 1.0
```

如果 `--reciprocal`，则 `(src, dst)` 和 `(dst, src)` 各生成一个 flow。

#### 2. `population_weighted`

逻辑：

1. 同样先随机配对。
2. 对每个 pair 计算原始需求。

原始权重：

```text
raw_weight = sqrt(pop_src * pop_dst)
```

归一化：

```text
demand_weight = raw_weight / median(raw_weight over scenario)
```

目的：

- 让该 scenario 中位数 demand weight 为 `1.0`。
- 保留相对需求差异。

当前 fallback：

- 因为现有 ground station 文件没有 population，`pop_src = pop_dst = 1.0`。
- 所以当前这个 model 会退化为全部 `demand_weight = 1.0`，并打印 warning。

#### 3. `gravity_model`

逻辑：

1. 同样先随机配对。
2. 根据 population 和地理距离计算 gravity-style demand。

距离：

```text
distance_km = haversine(src_lat, src_lon, dst_lat, dst_lon)
```

为了避免除零：

```text
distance_km = max(distance_km, 1.0)
```

原始权重：

```text
raw_weight = pop_src * pop_dst / distance_km^gravity_beta
```

默认：

```text
gravity_beta = 1.0
```

归一化：

```text
demand_weight = raw_weight / median(raw_weight over scenario)
```

当前 fallback：

- 因为没有 population 字段，`pop_src = pop_dst = 1.0`。
- 目前 gravity model 主要体现距离差异：距离越近，raw demand 越大。

#### 4. `regional_hotspot`

逻辑：

1. 同样先随机配对。
2. 根据 latitude / longitude 粗略推断 region。
3. 如果 pair 命中 hotspot corridor，则放大需求。

当前 coarse region 推断在 `scenarios.py::infer_region()` 中完成。示例 region：

- `North America`
- `Europe`
- `East Asia`
- `South Asia`
- `Latin America`
- `Africa`
- `Oceania`
- `Other`

默认 hotspot corridors：

```text
North America <-> Europe
East Asia <-> North America
Europe <-> East Asia
```

权重：

```text
if pair_region in hotspot_corridors:
    demand_weight = hotspot_multiplier
else:
    demand_weight = 1.0
```

默认：

```text
hotspot_multiplier = 3.0
```

### Routing policy 定义

所有 routing policy 都基于同一个代表性 graph snapshot。默认使用：

```text
project/satellite_networks/gen_data/<default_dataset>/graph/delete_0/graph_at_0.pkl
```

#### 1. `shortest_path`

基线策略。

边权：

```text
edge_weight = graph[u][v]["weight"]
```

即按链路距离最短路由。

#### 2. `stress_aware_two_pass`

两阶段策略。

Pass 1：

- 所有 flow 用 `shortest_path` 路由。
- 根据 Pass 1 的 paths 计算 link_load 和 link_stress。

Pass 2：

- 使用 Pass 1 的 link_stress 调整边权。

边权：

```text
edge_weight = distance_m * (1 + alpha * link_stress_from_pass_1)
```

默认：

```text
alpha = 2.0
```

解释：

- 这是一个 plausible link-stress-aware routing assumption。
- 不是真实 operator policy。
- 也不是完整的新 routing protocol。

#### 3. `k_shortest_load_balancing`

顺序处理 flow。

每个 flow：

1. 计算最多 `k` 条 shortest simple paths。
2. 根据当前已经路由的 flow 所产生的 link load，评估候选路径。
3. 选择当前 max link stress 最低的路径。
4. 如果 k-shortest 失败，则 fallback 到 shortest_path。

默认：

```text
k_paths = 3
```

候选路径评价核心：

```text
candidate_score = max((current_load[e] + flow.demand_weight) / link_capacity for e in path_edges)
```

tie-breaker：

```text
path_length_m
```

### Link load 和 link stress

这是本阶段最重要的数据逻辑。

#### edge key

图是无向图时，边 key 统一排序：

```text
edge_key(u, v) = tuple(sorted((u, v)))
```

如果未来图是有向图，则保留方向：

```text
edge_key(u, v) = (u, v)
```

#### link_load

`link_load` 不是随机生成的。

它由 traffic scenario 的 flow demand 和 routing path 叠加得到：

```text
link_load[e] = sum(flow.demand_weight for flow if e is in path(flow))
```

也就是：

```text
traffic scenario -> flows -> paths -> edge load
```

只有成功路由的 flow 会贡献 load。不可达 flow 不贡献 link load。

#### link_stress

`link_stress` 使用受控实验参数 `link_capacity` 计算：

```text
link_stress[e] = link_load[e] / link_capacity
```

默认：

```text
link_capacity = 10.0
```

解释：

- `link_capacity` 的单位是 demand units。
- 它不是 Mbps。
- `link_stress > 1.0` 表示在该实验参数下 over capacity。

### Latency 计算

#### path length

路径长度是 path 上所有边的 `weight` 之和：

```text
path_length_m = sum(graph[u][v]["weight"] for (u, v) in path_edges)
```

#### base latency

基础传播时延是 round-trip propagation latency proxy：

```text
base_latency_ns = 2 * path_length_m / speed_of_light * 1e9
```

其中：

```text
speed_of_light = 299792458.0 m/s
```

#### congestion-adjusted latency

拥塞修正时延是轻量 proxy：

```text
congested_latency_ns = base_latency_ns * (1 + beta * max_link_stress_on_path)
```

默认：

```text
beta = 0.5
```

解释：

- 这不是 ns-3 queueing simulation。
- 只是用于比较不同 traffic scenario 和 routing policy 下，link stress 对 latency 的影响方向。

### 输出文件

输出目录：

```text
project/outputs/risk_displacement/
```

该目录不提交到 git。

#### `flows_by_scenario.csv`

记录每个 scenario 生成的 flow：

- scenario name
- traffic model
- seed
- flow id
- src/dst ground station
- src/dst city
- demand weight

用途：

- 检查不同 traffic matrix 是否按预期变化。

#### `traffic_scenario_manifest.json`

记录 traffic generation 配置：

- ground station 文件
- ground station 数量
- 是否有 population
- traffic models
- seed 数量
- pair 数量
- reciprocal 设置

#### `per_policy_scenario_metrics.csv`

每个 scenario 和 routing policy 一行。

核心指标：

- `num_flows`
- `reachable_flows`
- `unreachable_flows`
- `total_demand`
- `avg_base_latency_ns`
- `p95_base_latency_ns`
- `avg_congested_latency_ns`
- `p95_congested_latency_ns`
- `max_link_stress`
- `avg_link_stress`
- `num_links_over_capacity`
- `top_10_link_load_share`

#### `path_summary_by_policy.csv`

每条 flow 在每种 policy 下的 path 和 latency：

- reachable
- path hops
- path length
- base latency
- congested latency
- path 上最大 link stress
- path 节点序列

#### `link_stress_by_policy.csv`

每条被使用的边在每个 scenario / policy 下的 load 和 stress：

- edge_u
- edge_v
- link_load
- link_stress
- over_capacity

用途：

- 验证 stress 来自 demand 和 path overlap。
- 检查哪些链路被 traffic scenario 压出来。

#### `first_step_manifest.json`

记录本次 run 的 graph path、输出目录、routing policy 和关键参数。

### 当前验证结果

已使用完整示例参数跑通：

```bash
conda run -n hypatia python run_risk_displacement_first_step.py \
  --traffic_models random_permutation_equal population_weighted gravity_model regional_hotspot \
  --num_seeds 3 \
  --num_pairs 50 \
  --reciprocal \
  --routing_policies shortest_path stress_aware_two_pass k_shortest_load_balancing \
  --link_capacity 10.0 \
  --alpha 2.0 \
  --beta 0.5 \
  --k_paths 3
```

输出规模：

- `flows_by_scenario.csv`：1200 条 flow + header。
- `per_policy_scenario_metrics.csv`：36 条 scenario-policy 组合 + header。
- `path_summary_by_policy.csv`：3600 条 flow-policy 组合 + header。
- `link_stress_by_policy.csv`：约 1 万条使用过的 link-policy 记录。

运行时会出现 population fallback warning，这是当前 ground station 文件没有 population 字段导致的预期行为。

