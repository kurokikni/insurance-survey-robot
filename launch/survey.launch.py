import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    package_dir = get_package_share_directory('insurance_survey_robot')
    gazebo_dir = get_package_share_directory('ros_gz_sim')
    world_path = os.path.join(package_dir, 'worlds', 'factory.sdf')

    return LaunchDescription([
        DeclareLaunchArgument('scenario', default_value='flood',
                              description='flood or normal'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_dir, 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': '-r ' + world_path}.items(),
        ),
        Node(
            package='ros_gz_bridge', executable='parameter_bridge',
            name='gazebo_bridge',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
                '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            ],
            output='screen',
        ),
        Node(
            package='insurance_survey_robot', executable='patrol',
            name='survey_patrol',
            parameters=[{'scenario': LaunchConfiguration('scenario')}],
            output='screen',
        ),
    ])
