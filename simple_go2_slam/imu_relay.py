import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu


class ImuRelay(Node):
    def __init__(self):
        super().__init__('imu_relay')
        self.declare_parameter('time_offset_seconds', 0.0)
        self.declare_parameter('auto_time_offset', True)
        self.declare_parameter('angular_velocity_z_stddev', 0.10)
        self.declare_parameter('target_frame', 'base_link')
        self.auto_time_offset = bool(
            self.get_parameter('auto_time_offset').value
        )
        self.time_offset = float(
            self.get_parameter('time_offset_seconds').value
        )
        self.offset_initialized = not self.auto_time_offset
        self.angular_velocity_z_variance = float(
            self.get_parameter('angular_velocity_z_stddev').value
        ) ** 2
        self.target_frame = str(
            self.get_parameter('target_frame').value
        )
        source_qos = QoSProfile(depth=10)
        source_qos.reliability = ReliabilityPolicy.RELIABLE
        self.publisher = self.create_publisher(
            Imu, '/imu_local', source_qos
        )
        self.subscription = self.create_subscription(
            Imu, '/utlidar/imu', self.callback, source_qos
        )

    def callback(self, msg: Imu):
        if not self.offset_initialized:
            stamp = rclpy.time.Time.from_msg(msg.header.stamp)
            if stamp.nanoseconds <= 0:
                self.get_logger().warning(
                    'Ignorando IMU con timestamp no válido durante la '
                    'calibración temporal.'
                )
                return
            self.time_offset = (
                self.get_clock().now() - stamp
            ).nanoseconds / 1e9
            self.offset_initialized = True
            self.get_logger().info(
                'Offset temporal de IMU calculado automáticamente: '
                f'{self.time_offset:.3f} s.'
            )

        corrected = Imu()
        corrected.header = msg.header
        corrected.header.frame_id = self.target_frame
        corrected.header.stamp = (
            rclpy.time.Time.from_msg(msg.header.stamp)
            + rclpy.time.Duration(seconds=self.time_offset)
        ).to_msg()
        corrected.angular_velocity = msg.angular_velocity
        corrected.angular_velocity_covariance[8] = (
            self.angular_velocity_z_variance
        )
        corrected.orientation_covariance[0] = -1.0
        corrected.linear_acceleration_covariance[0] = -1.0
        self.publisher.publish(corrected)


def main(args=None):
    rclpy.init(args=args)
    node = ImuRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
