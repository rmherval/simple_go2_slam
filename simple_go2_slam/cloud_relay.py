import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from rclpy.qos import qos_profile_sensor_data

class CloudRelay(Node):
    def __init__(self):
        super().__init__('cloud_relay')
        self.declare_parameter('time_offset_seconds', 0.0)
        self.declare_parameter('auto_time_offset', True)
        self.auto_time_offset = bool(
            self.get_parameter('auto_time_offset').value
        )
        self.time_offset = float(
            self.get_parameter('time_offset_seconds').value
        )
        self.offset_initialized = not self.auto_time_offset
        self.pub = self.create_publisher(
            PointCloud2,
            '/cloud_local',
            qos_profile_sensor_data
        )
        self.sub = self.create_subscription(
            PointCloud2,
            '/utlidar/cloud_deskewed',
            self.callback,
            qos_profile_sensor_data
        )
        self.get_logger().info(
            'CloudRelay activo: calibración temporal automática='
            f'{self.auto_time_offset}.'
        )

    def callback(self, msg: PointCloud2):
        if not self.offset_initialized:
            stamp = rclpy.time.Time.from_msg(msg.header.stamp)
            if stamp.nanoseconds <= 0:
                self.get_logger().warning(
                    'Ignorando nube con timestamp no válido durante la '
                    'calibración temporal.'
                )
                return
            self.time_offset = (
                self.get_clock().now() - stamp
            ).nanoseconds / 1e9
            self.offset_initialized = True
            self.get_logger().info(
                'Offset temporal calculado automáticamente: '
                f'{self.time_offset:.3f} s.'
            )
        offset = rclpy.time.Duration(seconds=self.time_offset)
        msg.header.stamp = (
            rclpy.time.Time.from_msg(msg.header.stamp) + offset
        ).to_msg()
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CloudRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()