import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('simple_go2_slam')
    param_file = os.path.join(pkg_dir, 'config', 'laserscan_params.yaml')
    rviz_config_file = os.path.join(pkg_dir, 'rviz', 'slam.rviz')
    time_offset_seconds = 3657.0

    return LaunchDescription([
        # 1. Cloud Relay
        Node(
            package='simple_go2_slam',
            executable='cloud_relay',
            name='cloud_relay',
            parameters=[{
                'time_offset_seconds': time_offset_seconds
            }]
        ),

        # 2. Odometría del robot -> TF odom -> base_link
        Node(
            package='simple_go2_slam',
            executable='odom_to_tf',
            name='odom_to_tf',
            parameters=[{
                'time_offset_seconds': time_offset_seconds
            }]
        ),

        # 3. Robot marker for RViz
        Node(
            package='simple_go2_slam',
            executable='robot_marker',
            name='robot_marker'
        ),

        # 4. Pointcloud to LaserScan
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            remappings=[
                ('cloud_in', '/cloud_local'),
                ('scan', '/scan')
            ],
            parameters=[param_file]
        ),

        # 5. SLAM Toolbox
        Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            name='slam_toolbox',
            parameters=[{
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',
                'scan_topic': '/scan',
                'mode': 'mapping',
                'use_sim_time': False,
                'qos_overrides./scan.subscription.reliability': 'best_effort',
                'transform_publish_period': 0.05,
                'map_update_interval': 1.0,
                'scan_queue_size': 20,
                'throttle_scans': 1,
                'minimum_travel_distance': 0.10,
                'minimum_travel_heading': 0.10,
                'minimum_time_interval': 0.10,
                'min_laser_range': 0.45,
                'max_laser_range': 4.0,
                'do_loop_closing': True,
                'loop_search_maximum_distance': 10.0,
                'loop_match_minimum_response_coarse': 0.30,
                'loop_match_minimum_response_fine': 0.40,
                'transform_timeout': 0.3,
                'tf_buffer_duration': 30.0,
                'distance_variance_penalty': 0.5,
                'angle_variance_penalty': 1.0,
                'resolution': 0.05
            }]
        ),

        # 6. RViz2 con la configuración precargada
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file]
        )
    ])