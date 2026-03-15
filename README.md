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

当 AprilTag **贴在墙上**作为固定参考时，按下面步骤设定世界坐标系和 `tags_config.yaml` 中的参数，可避免混淆、便于后续使用 `/camera/world_pose` 的数据。

### 1. 约定世界坐标系（建议）

- **原点**：选一面墙上的**某一个 Tag 的中心**作为世界原点 `(0, 0, 0)`。
- **轴向**（任选一种，与你的应用一致即可）：
  - **Z 轴**：垂直于墙面、指向**房间内**（即从墙指向相机通常所在的一侧）。
  - **X 轴**：沿墙面水平方向（例如向右）。
  - **Y 轴**：沿墙面竖直方向（例如向上），与 X、Z 成右手系。

这样，相机在房间内移动时，得到的 `position.x / y / z` 就是相对这面墙的坐标，便于理解与后续建图/导航。

### 2. 只贴一个 Tag 时（最简单）

- 在 `tags_world_coordinates` 里只保留这一个 tag（例如 `tag_0`）。
- **id**：与该 Tag 打印的 ID 一致（解码得到几就填几）。
- **位置**：把它当作世界原点，填：
  ```yaml
  x: 0.0
  y: 0.0
  z: 0.0
  ```
- **姿态**：Tag 水平贴墙、不旋转（即 Tag 的边与上面约定的 X/Y 平行）时，填：
  ```yaml
  roll: 0.0
  pitch: 0.0
  yaw: 0.0
  ```
- **tag_size**：用卷尺量该 Tag **黑边边长**（整块正方形边长），单位米。例如 13.25 cm → `tag_size: 0.1325`。

此时世界系与该 Tag 的本地系一致，相机位姿就是「相对这面墙」的位姿。

### 3. 同一面墙上贴多个 Tag 时

- **选一个 Tag 作为原点**（如 `tag_0`）：按上面方式设为 `(0, 0, 0)`，`roll/pitch/yaw` 全 0（若水平贴、无旋转）。
- **其它 Tag**：用卷尺量**相对原点 Tag 中心**的偏移（单位：米），按你约定的轴向填入 `x, y, z`：
  - 沿墙面水平方向（如向右）的偏移 → **x**
  - 沿墙面竖直方向（如向上）的偏移 → **y**
  - 若在同一面墙、同一平面，**z 保持 0**。
- **姿态**：
  - 若与原点 Tag 同向贴（都是“正着贴”、边平行），则 `roll: 0, pitch: 0, yaw: 0`。
  - 若某个 Tag 绕**垂直于墙的轴**旋转了（例如竖着贴），则只改 **yaw**：旋转 90° 填 `yaw: 90.0`，180° 填 `yaw: 180.0`，以此类推。
  - 若 Tag 有倾斜（绕墙面内轴旋转），再按需设 **roll** 或 **pitch**（单位均为度）。

### 4. 测量与填写示例（单墙、两 Tag）

- 原点 Tag（id=0）：中心为世界原点，水平贴墙。
  ```yaml
  tag_0:
    id: 0
    x: 0.0
    y: 0.0
    z: 0.0
    roll: 0.0
    pitch: 0.0
    yaw: 0.0
  ```
- 另一个 Tag（id=1）：量得在原点 Tag **右侧 1.0 m、上方 0.5 m**，同向贴：
  ```yaml
  tag_1:
    id: 1
    x: 1.0
    y: 0.5
    z: 0.0
    roll: 0.0
    pitch: 0.0
    yaw: 0.0
  ```

若 id=1 的 Tag 是**竖着贴**（相对 id=0 绕 Z 转 90°），则把 `yaw: 0.0` 改为 `yaw: 90.0`。

### 5. 小结

| 步骤 | 做法 |
|------|------|
| 定原点 | 选一面墙上的一个 Tag 中心为 (0, 0, 0) |
| 定轴向 | 建议 Z 指房间内，X 水平，Y 竖直，右手系 |
| 量 tag_size | 尺子量黑边边长，单位米，填到 `apriltag_settings.tag_size` |
| 单 Tag | 该 Tag 填 x,y,z=0，roll,pitch,yaw=0（水平贴时） |
| 多 Tag | 量相对原点的 x/y/z（同墙则 z=0），同向贴则 roll/pitch/yaw=0，旋转则改 yaw（度） |

按上述方式设定后，`/camera/world_pose` 中的位置和姿态就是**相机相对于这面墙上的 Tag 所定义的世界系**的 6DoF 位姿。

---

## License

按项目仓库约定使用。
