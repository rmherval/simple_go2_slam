import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'simple_go2_slam'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='user@todo.todo',
    description='Simple Go2 SLAM',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'odom_to_tf = simple_go2_slam.odom_to_tf:main',
            'cloud_relay = simple_go2_slam.cloud_relay:main',
            'robot_marker = simple_go2_slam.robot_marker:main',
        ],
    },
)