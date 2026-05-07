cmake_minimum_required(VERSION 3.8)
project(rover_description)

find_package(ament_cmake REQUIRED)

install(
    DIRECTORY
        config
        launch
        meshes
        robots
        rviz
        urdf
    DESTINATION share/${PROJECT_NAME}
    )


    install(
    PROGRAMS
        scripts/cmd_vel_to_stamped.py
        scripts/record_analysis.py
    DESTINATION lib/${PROJECT_NAME}
)

ament_package()