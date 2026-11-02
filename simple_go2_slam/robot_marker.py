import rclpy
from geometry_msgs.msg import Point
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener
from visualization_msgs.msg import Marker


class RobotMarker(Node):
    def __init__(self):
        super().__init__('robot_marker')
        self.publisher = self.create_publisher(Marker, '/robot_marker', 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(0.1, self.publish_marker)

    def publish_marker(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time(),
                timeout=Duration(seconds=0.05),
            )
        except TransformException:
            return

        marker = Marker()
        marker.header = transform.header
        marker.ns = 'robot'
        marker.id = 0
        marker.type = Marker.ARROW
        marker.action = Marker.ADD
        marker.pose.orientation = transform.transform.rotation
        marker.scale.x = 0.35
        marker.scale.y = 0.05
        marker.scale.z = 0.05
        marker.color.r = 0.1
        marker.color.g = 0.9
        marker.color.b = 0.1
        marker.color.a = 1.0
        marker.lifetime = Duration(seconds=0.3).to_msg()

        marker.pose.position = Point(
            x=transform.transform.translation.x,
            y=transform.transform.translation.y,
            z=transform.transform.translation.z,
        )
        self.publisher.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = RobotMarker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
