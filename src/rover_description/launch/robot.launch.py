from os import environ, pathsep
from os.path import join, dirname

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_jsp_gui = LaunchConfiguration("use_jsp_gui")
    launch_rviz = LaunchConfiguration("launch_rviz")
    launch_controllers = LaunchConfiguration("launch_controllers")

    declare_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation time"
    )

    declare_jsp_gui = DeclareLaunchArgument(
        "use_jsp_gui",
        default_value="false",
        description="Launch joint_state_publisher_gui"
    )

    declare_launch_rviz = DeclareLaunchArgument(
        "launch_rviz",
        default_value="true",
        description="Launch RViz"
    )

    declare_launch_controllers = DeclareLaunchArgument(
        "launch_controllers",
        default_value="true",
        description="Load ros2_control controllers automatically"
    )

    rover_pkg = get_package_share_directory("rover_description")
    moveit_pkg = get_package_share_directory("rover_moveit_config")
    world_pkg = get_package_share_directory("urjc_excavation_world")

    moveit_config = MoveItConfigsBuilder(
        "robot_Practica2",
        package_name="rover_moveit_config"
    ).to_moveit_configs()

    resource_root = dirname(rover_pkg)

    resource_path = resource_root
    if "GZ_SIM_RESOURCE_PATH" in environ:
        resource_path = resource_path + pathsep + environ["GZ_SIM_RESOURCE_PATH"]

    model_path = resource_root
    if "GZ_SIM_MODEL_PATH" in environ:
        model_path = model_path + pathsep + environ["GZ_SIM_MODEL_PATH"]

    set_resource_path = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_path)
    set_model_path = SetEnvironmentVariable("GZ_SIM_MODEL_PATH", model_path)

    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(world_pkg, "launch", "urjc_excavation_msr.launch.py")
        )
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            {"use_sim_time": use_sim_time},
        ],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-model", "robot_Practica2",
            "-topic", "robot_description",
            "-use_sim_time", "true",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.85",
        ],
    )

    delayed_spawn = TimerAction(
        period=3.0,
        actions=[spawn_robot]
    )

    controllers_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(rover_pkg, "launch", "robot_controllers.launch.py")
        ),
        condition=IfCondition(launch_controllers),
    )

    delayed_controllers = TimerAction(
        period=6.0,
        actions=[controllers_launch]
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", join(moveit_pkg, "config", "moveit.rviz")],
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},
        ],
        output="screen",
        condition=IfCondition(launch_rviz),
    )

    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {"config_file": join(rover_pkg, "config", "bridge.yaml")},
            {"use_sim_time": use_sim_time},
        ],
        output="screen",
    )

    cmd_vel_stamped_node = Node(
        package="rover_description",
        executable="cmd_vel_to_stamped.py",
        parameters=[
            {"use_sim_time": use_sim_time},
            {"input_topic": "/cmd_vel"},
            {"output_topic": "/rover_base_control/cmd_vel"},
            {"frame_id": "base_footprint"},
        ],
        output="screen",
    )

    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
        condition=IfCondition(use_jsp_gui),
    )

    return LaunchDescription([
        declare_sim_time,
        declare_jsp_gui,
        declare_launch_rviz,
        declare_launch_controllers,

        set_model_path,
        set_resource_path,

        world_launch,
        robot_state_publisher,
        bridge_node,
        delayed_spawn,
        delayed_controllers,
        rviz_node,
        cmd_vel_stamped_node,
        joint_state_publisher_gui,
    ])