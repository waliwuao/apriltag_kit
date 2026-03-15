# ApriltagKit

基于 AprilTag 的相机标定、检测与位姿估计库，支持 ROS2 发布相机在世界坐标系下的 6DoF 位姿（位置 + 四元数姿态）。

## 项目结构

```
apriltag-kit/
├── apriltag_kit/           # 核心库
│   ├── __init__.py
│   ├── calibration.py      # 棋盘格标定 (CameraCalibrator)
│   ├── detection.py        # AprilTag 检测 (BaseDetector, StaticDetector, LiveDetector)
│   └── visualization.py   # 绘制 tag 框与坐标轴
├── example/                # ROS2 示例
│   ├── config/
│   │   └── tags_config.yaml
│   ├── apriltag_ros_node.py
│   └── apriltag_launch.py
├── camera_calibration.npz  # 标定结果（需自行标定或放置）
├── requirements.txt
└── README.md
```

## 安装

```bash
pip install -r requirements.txt
```

运行 `example/` 下的 ROS2 节点前，需安装并 source ROS2（如 Humble），且使用 **Python 3.10**（与 ROS2 Humble 匹配）。

## 标定

将棋盘格照片放入某文件夹（如 `pic/`），在项目根目录执行：

```python
from apriltag_kit import CameraCalibrator
cal = CameraCalibrator(square_size=0.02)  # 棋盘格一格边长，单位：米
cal.calibrate("pic", "camera_calibration.npz")
```

生成的 `camera_calibration.npz` 放在项目根目录，供检测与 example 使用。

## 运行 Example（ROS2 节点）

```bash
source /opt/ros/humble/setup.bash
cd /path/to/apriltag-kit
python3.10 example/apriltag_ros_node.py
```

或使用 launch 脚本（内部会调用节点）：

```bash
python3.10 example/apriltag_launch.py
```

查看发布的位姿：

```bash
ros2 topic echo /camera/world_pose
```

---

## 发布的 Topic 数据含义

节点默认发布到 **`/camera/world_pose`**（可在 config 中修改），消息类型为 **`geometry_msgs/PoseStamped`**。每条消息表示**当前相机在世界坐标系下的位姿**（检测到配置中的某个 AprilTag 时计算得到）。

你提供的一条示例消息如下，各字段含义如下。

### header（头部）

| 字段 | 含义 |
|------|------|
| **header.stamp** | ROS 时间戳。`sec` 为秒，`nanosec` 为纳秒，表示该位姿对应的采集/计算时刻。 |
| **header.frame_id** | 参考坐标系名称，固定为 `"world"`。表示 pose 中的位置与姿态都是相对于「世界坐标系」的。 |

### pose（位姿）

| 字段 | 含义 |
|------|------|
| **pose.position.x** | 相机光心在世界坐标系下的 X 坐标，单位：**米**。 |
| **pose.position.y** | 相机光心在世界坐标系下的 Y 坐标，单位：**米**。 |
| **pose.position.z** | 相机光心在世界坐标系下的 Z 坐标，单位：**米**。 |

即 `(x, y, z)` 表示**相机在世界系中的位置**。

| 字段 | 含义 |
|------|------|
| **pose.orientation.x** | 四元数分量 **qx**，表示相机在世界系下的姿态（旋转）。 |
| **pose.orientation.y** | 四元数分量 **qy**。 |
| **pose.orientation.z** | 四元数分量 **qz**。 |
| **pose.orientation.w** | 四元数分量 **qw**。 |

四元数 (qx, qy, qz, qw) 描述**相机坐标系相对世界坐标系的旋转**，符合 ROS 惯例（可用于 tf、RViz 等）。若需要欧拉角或旋转矩阵，需自行从四元数转换。

### 示例解读

对你给的这条消息：

- **位置**：相机在世界系中约在 `(-0.0067, 0.0232, 0.268)` 米，即略偏左、略偏上、距离原点约 26.8 cm。
- **姿态**：由 `orientation` 的四元数表示相机朝向；`frame_id: world` 表示上述位置与姿态都以你在 `tags_config.yaml` 里定义的「世界坐标系」为参考。

---

## 配置文件参数说明（example/config/tags_config.yaml）

### apriltag_settings（AprilTag 与相机全局设置）

| 参数 | 含义 |
|------|------|
| **family** | AprilTag 码族，如 `"tag36h11"`。需与打印的 tag 类型一致。 |
| **tag_size** | 单个 AprilTag **整块 tag 的边长**，单位：**米**。例如 13.25 cm 填 `0.1325`。 |
| **camera_id** | 摄像头设备编号。通常 `0` 为默认/内置摄像头，`1` 为外接第一个。 |
| **resolution** | 可选。设为 `"auto"` 时由节点内逻辑尝试使用较高分辨率；若不需要可删或改。 |
| **publish_topic** | 发布的 ROS topic 名称，如 `"/camera/world_pose"`。 |

### tags_world_coordinates（每个 Tag 在世界系中的位姿）

每个 tag 的配置项（如 `tag_0`、`tag_1`）：

| 参数 | 含义 |
|------|------|
| **id** | AprilTag 的 ID（解码得到的数字），与物理 tag 一一对应。 |
| **x** | 该 Tag **中心**在世界坐标系下的 X 坐标，单位：**米**。 |
| **y** | 该 Tag 中心在世界系下的 Y 坐标，单位：**米**。 |
| **z** | 该 Tag 中心在世界系下的 Z 坐标，单位：**米**。 |
| **roll** | 该 Tag 在世界系下的绕 X 轴旋转角，单位：**度**。 |
| **pitch** | 该 Tag 在世界系下的绕 Y 轴旋转角，单位：**度**。 |
| **yaw** | 该 Tag 在世界系下的绕 Z 轴旋转角，单位：**度**。 |

(roll, pitch, yaw) 定义该 Tag 的**姿态**；若 Tag 平面朝上、边与世界轴对齐，可全部设为 0。例如 `yaw: 90.0` 表示该 Tag 绕世界 Z 轴转 90°。

**注意**：世界坐标系的原点与轴向由你自己在布置 Tag 时定义；节点会根据这些参数和检测到的 tag 位姿，计算并发布相机在该世界系下的 `position` 与 `orientation`。

---

## AprilTag 贴墙时的初始参数设定指南

当 AprilTag **贴在墙上**作为固定参考时，只要在配置里正确设定世界系和每个 Tag 的位姿，节点就能**正确解析**出相机在**该世界系**下的坐标。下面采用常见的「**XY 为地板平面、Z 为竖直向上**」的惯例来设定。

### 1. 世界坐标系约定（XY 地板，Z 竖直向上）

与常见机器人/建图习惯一致，建议：

- **世界原点**：选一面墙上的**某一个 Tag 的中心**作为世界原点 `(0, 0, 0)`。可理解为该点在「地板平面 + 墙」的交线附近（Tag 中心所在水平面与地板的交线，或直接把 Tag 中心投影到地板上的点，依你测量方式而定；若 Tag 离地不高，可近似为 Tag 中心即原点）。
- **世界轴向**：
  - **Z 轴**：**竖直向上**（重力反方向）。
  - **X、Y 轴**：在**水平面（地板平面）**内，互相垂直，右手系。例如 X 沿墙向右、Y 指向房间内；或 X 指东、Y 指北等，与你的应用一致即可。

这样 `/camera/world_pose` 里的 `position.z` 表示**高度**，`position.x / y` 表示在**水平面上的位置**，便于与地图、导航等对接。

### 2. 贴墙的 Tag 能否正确解析？可以

节点内部用的是「Tag 在相机系下的位姿 → 相机在 Tag 系下 → 再变换到世界系」。**世界系**完全由你在 `tags_config.yaml` 里给的 `(x, y, z, roll, pitch, yaw)` 定义。只要这些参数和你约定的「XY 地板、Z 向上」一致，**贴墙的 AprilTag 也能正确解析出该世界系下的相机坐标**。

检测库给出的 Tag 本地系一般是：**Tag 平面为 XY，Z 轴由 Tag 指向相机**。所以当 Tag **贴在竖直墙面上**时（正面朝房间）：

- Tag 的 **Z** ≈ 从墙指向房间内（**水平**）；
- Tag 的 **X、Y** 在墙面内（一个沿墙水平、一个沿墙**竖直向上**）。

要得到「世界 Z = 竖直向上」，就需要用配置里的 **roll / pitch / yaw** 把「Tag 系」旋转成「世界系」。下面给出一种常用设法和对应参数。

### 3. 只贴一个 Tag 时（最简单）

- **id**：与该 Tag 解码得到的 ID 一致。
- **位置**：作为世界原点：
  ```yaml
  x: 0.0
  y: 0.0
  z: 0.0
  ```
- **姿态（关键）**：要让世界系变成 **XY 地板、Z 向上**，需要根据 Tag 在墙上的朝向设 roll/pitch/yaw。若 Tag **正贴**（不歪、不竖贴），且约定：
  - Tag 的 **Y 轴**沿墙**竖直向上**，
  - Tag 的 **Z 轴**从墙指向房间内（水平），  
  则可通过「绕 Tag 本地 X 轴转 -90°」把 Tag 的 Y 转到世界 Z（向上）。推荐先试：
  ```yaml
  roll: -90.0
  pitch: 0.0
  yaw: 0.0
  ```
  此时世界：**Z = 竖直向上**，X/Y 在水平面。若实际贴法不同（例如 Tag 竖贴或转了 90°），再在 `yaw` 上加减 90° 微调水平朝向即可。
- **tag_size**：用卷尺量该 Tag **黑边边长**，单位米（如 13.25 cm → `0.1325`）。

这样配置后，节点会正确输出相机在「XY 地板、Z 向上」世界系下的位姿。

### 4. 同一面墙上多个 Tag 时

- **选一个 Tag 为原点**：`x,y,z = 0,0,0`，按上面设好 `roll: -90, pitch: 0, yaw: 0`（或你验证过的贴墙参数）。
- **其它 Tag**：用卷尺量**相对原点 Tag 中心**的偏移（单位：米），在**世界系**下填入：
  - 沿世界 **X** 方向偏移 → **x**
  - 沿世界 **Y** 方向偏移 → **y**
  - 沿世界 **Z** 方向偏移（高度差）→ **z**  
  同一面墙、同一高度则 z 相同；若另一个 Tag 在原 Tag 正上方 0.5 m，则 z 比原点多 0.5。
- **姿态**：与原点 Tag **同向贴**（都是正贴、边平行）时，用相同的 roll/pitch/yaw（如 `roll: -90, pitch: 0, yaw: 0`）。若某个 Tag 在墙上**竖着贴**（相对原点绕墙法向转 90°），则在该 Tag 上把 **yaw** 加或减 90°（如 `yaw: 90.0`）。

### 5. 测量与填写示例（单墙、两 Tag，世界 XY 地板 Z 向上）

- 原点 Tag（id=0）：世界原点，正贴墙。
  ```yaml
  tag_0:
    id: 0
    x: 0.0
    y: 0.0
    z: 0.0
    roll: -90.0
    pitch: 0.0
    yaw: 0.0
  ```
- 另一个 Tag（id=1）：量得在**世界系**下为「原点右侧 1.0 m、向房间内 0.5 m、高度相同」：
  ```yaml
  tag_1:
    id: 1
    x: 1.0
    y: 0.5
    z: 0.0
    roll: -90.0
    pitch: 0.0
    yaw: 0.0
  ```
  若 id=1 在原点**正上方 0.5 m**、水平位置相同，则 `x: 0.0, y: 0.0, z: 0.5`，roll/pitch/yaw 同上。

### 6. 小结

| 步骤 | 做法 |
|------|------|
| 世界系 | **XY = 地板平面，Z = 竖直向上**；原点可选墙上某 Tag 中心（或其在水平面上的投影） |
| 贴墙能否正确解析 | **可以**。通过 (x,y,z,roll,pitch,yaw) 把 Tag 系对齐到世界系即可 |
| 单 Tag 正贴墙 | 原点 (0,0,0)，常用 `roll: -90, pitch: 0, yaw: 0` 得到 Z 向上 |
| 多 Tag | 相对原点在世界系下量 x/y/z；同向贴用相同 roll/pitch/yaw，竖贴等改 yaw |
| tag_size | 尺子量黑边边长（米），填到 `apriltag_settings.tag_size` |

按上述方式设定后，`/camera/world_pose` 中的 `position.x / y` 为水平面坐标，`position.z` 为高度，与「XY 地板、Z 竖直」的惯例一致。

---

## License

按项目仓库约定使用。
