from launch import LaunchDescription
from launch_ros.actions import Node


def spawner(controller_name):
    return Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            controller_name,
            "--controller-manager", "/controller_manager",
            "--controller-manager-timeout", "120",
        ],
        output="screen",
    )


def generate_launch_description():
    joint_state_broadcaster = spawner("joint_state_broadcaster")
    base_controller = spawner("rover_base_control")
    scara_controller = spawner("scara_controller")
    gripper_controller = spawner("gripper_controller")

    return LaunchDescription([
        joint_state_broadcaster,
        base_controller,
        scara_controller,
        gripper_controller,
    ])