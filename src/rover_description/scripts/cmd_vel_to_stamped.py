#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class CmdVelToStamped(Node):
    def __init__(self):
        super().__init__("cmd_vel_to_stamped")

        self.declare_parameter("input_topic", "/cmd_vel")
        self.declare_parameter("output_topic", "/rover_base_control/cmd_vel")
        self.declare_parameter("frame_id", "base_footprint")

        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value
        self.frame_id = self.get_parameter("frame_id").value

        self.sub = self.create_subscription(Twist, input_topic, self.cb, 10)
        self.pub = self.create_publisher(TwistStamped, output_topic, 10)

    def cb(self, msg: Twist):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = 'base_footprint'

        # Invertimos solo el eje lineal X
        out.twist.linear.x = -msg.linear.x
        out.twist.linear.y = msg.linear.y
        out.twist.linear.z = msg.linear.z

        out.twist.angular.x = msg.angular.x
        out.twist.angular.y = msg.angular.y
        out.twist.angular.z = msg.angular.z

        self.pub.publish(out)


def main():
    rclpy.init()
    node = CmdVelToStamped()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()