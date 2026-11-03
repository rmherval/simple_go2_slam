import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


class OdomRelay(Node):
    def __init__(self):
        super().__init__('odom_relay')
        self.declare_parameter('time_offset_seconds', 0.0)
        self.declare_parameter('auto_time_offset', True)
        self.declare_parameter('pose_xy_stddev', 0.05)
        self.declare_parameter('pose_yaw_stddev', 0.0872665)
        self.declare_parameter('twist_xy_stddev', 0.10)
        self.declare_parameter('twist_yaw_stddev', 0.10)
        self.auto_time_offset = bool(
            self.get_parameter('auto_time_offset').value
        )
        self.time_offset = float(
            self.get_parameter('time_offset_seconds').value
        )
        self.pose_xy_variance = float(
            self.get_parameter('pose_xy_stddev').value
        ) ** 2
        self.pose_yaw_variance = float(
            self.get_parameter('pose_yaw_stddev').value
        ) ** 2
        self.twist_xy_variance = float(
            self.get_parameter('twist_xy_stddev').value
        ) ** 2
        self.twist_yaw_variance = float(
            self.get_parameter('twist_yaw_stddev').value
        ) ** 2
        self.offset_initialized = not self.auto_time_offset
        self.publisher = self.create_publisher(
            Odometry,
            '/odom_local',
            qos_profile_sensor_data,
        )
        self.subscription = self.create_subscription(
            Odometry,
            '/utlidar/robot_odom',
            self.callback,
            qos_profile_sensor_data,
        )

    def callback(self, msg: Odometry):
        if not self.offset_initialized:
            stamp = rclpy.time.Time.from_msg(msg.header.stamp)
            if stamp.nanoseconds <= 0:
                self.get_logger().warning(
                    'Ignorando odometría con timestamp no válido durante '
                    'la calibración temporal.'
                )
                return
            self.time_offset = (
                self.get_clock().now() - stamp
            ).nanoseconds / 1e9
            self.offset_initialized = True
            self.get_logger().info(
                'Offset temporal de odometría calculado automáticamente: '
                f'{self.time_offset:.3f} s.'
            )

        corrected = Odometry()
        corrected.header = msg.header
        corrected.header.stamp = (
            rclpy.time.Time.from_msg(msg.header.stamp)
            + rclpy.time.Duration(seconds=self.time_offset)
        ).to_msg()
        corrected.child_frame_id = msg.child_frame_id or 'base_link'
        corrected.pose = msg.pose
        corrected.twist = msg.twist
        corrected.pose.covariance[0] = self.pose_xy_variance
        corrected.pose.covariance[7] = self.pose_xy_variance
        corrected.pose.covariance[35] = self.pose_yaw_variance
        corrected.twist.covariance[0] = self.twist_xy_variance
        corrected.twist.covariance[7] = self.twist_xy_variance
        corrected.twist.covariance[35] = self.twist_yaw_variance
        self.publisher.publish(corrected)


def main(args=None):
    rclpy.init(args=args)
    node = OdomRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
