import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from rclpy.qos import qos_profile_sensor_data

class OdomToTf(Node):
    def __init__(self):
        super().__init__('odom_to_tf_custom')
        self.declare_parameter('time_offset_seconds', 0.0)
        self.declare_parameter('auto_time_offset', True)
        self.auto_time_offset = bool(
            self.get_parameter('auto_time_offset').value
        )
        self.time_offset = float(
            self.get_parameter('time_offset_seconds').value
        )
        self.offset_initialized = not self.auto_time_offset
        self.tf_broadcaster = TransformBroadcaster(self)
        self.sub = self.create_subscription(
            Odometry,
            '/utlidar/robot_odom',
            self.odom_callback,
            qos_profile_sensor_data
        )
        self.get_logger().info(
            'Publicador odom -> base_link activo: calibración temporal '
            f'automática={self.auto_time_offset}.'
        )

    def odom_callback(self, msg: Odometry):
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
                'Offset temporal calculado automáticamente: '
                f'{self.time_offset:.3f} s.'
            )
        t = TransformStamped()
        offset = rclpy.time.Duration(seconds=self.time_offset)
        t.header.stamp = (
            rclpy.time.Time.from_msg(msg.header.stamp) + offset
        ).to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()