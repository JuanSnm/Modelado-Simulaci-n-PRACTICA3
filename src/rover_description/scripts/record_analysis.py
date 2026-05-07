#!/usr/bin/env python3

import csv
import os

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState, Imu


class AnalysisRecorder(Node):
    def __init__(self):
        super().__init__('analysis_recorder')

        self.pick_joints = [
            'arm_1_link_joint',
            'arm_2_link_joint',
            'arm_3_link_joint',
            'arm_4_link_joint',
            'gripper_1_link_joint',
            'gripper_2_link_joint',
        ]

        self.wheel_joints = [
            'wheelA_1_link_joint',
            'wheelA_2_link_joint',
            'wheelA_3_link_joint',
            'wheelB_1_link_joint',
            'wheelB_2_link_joint',
            'wheelB_3_link_joint',
        ]

        self.latest_joint_state = None
        self.latest_imu = None
        self.t0 = None

        self.output_dir = os.path.expanduser('~/analysis_data')
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, 'analysis.csv')

        self.csv_file = open(self.output_file, 'w', newline='')
        self.writer = csv.writer(self.csv_file)

        header = [
            't',
            'arm_1_effort',
            'arm_2_effort',
            'arm_3_effort',
            'arm_4_effort',
            'gripper_1_effort',
            'gripper_2_effort',
            'G_parcial',
            'wheelA_1_pos',
            'wheelA_2_pos',
            'wheelA_3_pos',
            'wheelB_1_pos',
            'wheelB_2_pos',
            'wheelB_3_pos',
            'imu_ax',
            'imu_ay',
            'imu_az',
        ]
        self.writer.writerow(header)

        self.create_subscription(JointState, '/joint_states', self.joint_cb, 50)
        self.create_subscription(Imu, '/imu/data', self.imu_cb, 50)

        self.timer = self.create_timer(0.05, self.record_sample)

        self.get_logger().info(f'Grabando datos en: {self.output_file}')

    def joint_cb(self, msg: JointState):
        self.latest_joint_state = msg

    def imu_cb(self, msg: Imu):
        self.latest_imu = msg

    def record_sample(self):
        if self.latest_joint_state is None or self.latest_imu is None:
            return

        now = self.get_clock().now().nanoseconds / 1e9
        if self.t0 is None:
            self.t0 = now
        t = now - self.t0

        name_to_pos = {}
        name_to_effort = {}

        for i, name in enumerate(self.latest_joint_state.name):
            if i < len(self.latest_joint_state.position):
                name_to_pos[name] = self.latest_joint_state.position[i]
            if i < len(self.latest_joint_state.effort):
                name_to_effort[name] = self.latest_joint_state.effort[i]

        efforts = [name_to_effort.get(j, 0.0) for j in self.pick_joints]
        g_parcial = sum(abs(e) for e in efforts)

        wheel_positions = [name_to_pos.get(j, 0.0) for j in self.wheel_joints]

        imu_ax = self.latest_imu.linear_acceleration.x
        imu_ay = self.latest_imu.linear_acceleration.y
        imu_az = self.latest_imu.linear_acceleration.z

        row = [
            t,
            efforts[0],
            efforts[1],
            efforts[2],
            efforts[3],
            efforts[4],
            efforts[5],
            g_parcial,
            wheel_positions[0],
            wheel_positions[1],
            wheel_positions[2],
            wheel_positions[3],
            wheel_positions[4],
            wheel_positions[5],
            imu_ax,
            imu_ay,
            imu_az,
        ]
        self.writer.writerow(row)
        self.csv_file.flush()

    def destroy_node(self):
        try:
            self.csv_file.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AnalysisRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()