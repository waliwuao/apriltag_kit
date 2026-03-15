from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='apriltag_example',
            executable='apriltag_ros_node.py',
            name='apriltag_pose_node',
            output='screen',
            parameters=[{
                'use_sim_time': False
            }]
        )
    ])


if __name__ == '__main__':
    # 允许直接运行此文件进行测试（无需 ROS2 launch）
    # ROS2 Humble 仅支持 Python 3.10，若在 conda 下请用 python3.10 运行
    import sys
    import subprocess
    import shutil
    script_path = os.path.join(os.path.dirname(__file__), 'apriltag_ros_node.py')
    python_cmd = shutil.which('python3.10') or sys.executable
    subprocess.run([python_cmd, script_path], check=False)
