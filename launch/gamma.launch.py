"""
gamma の実機を動かす: robot_bridge（実機のシリアル）+ 操作ノード（+ 任意で rviz）.

偽ファームで動かすときは gamma_sim.launch.py。構成の違いは device だけ。
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command, EqualsSubstitution, FindExecutable, LaunchConfiguration, PathJoinSubstitution)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bridge_config = os.path.join(
        get_package_share_directory('rabbits_bridge'), 'config', 'gamma.yaml')
    interface_launch = os.path.join(
        get_package_share_directory('rabbits_interface'), 'launch')

    args = [
        DeclareLaunchArgument(
            'device', default_value='/dev/ttyUSB0',
            description='ファームのシリアル（USB-UART は /dev/ttyUSB0、Jetson の UART は /dev/ttyTHS1）'),
        DeclareLaunchArgument(
            'input', default_value='gamepad',
            description='操作の入力: gamepad | game_client | none'),
        DeclareLaunchArgument(
            'rviz', default_value='false',
            description='robot_state_publisher と rviz2 も起動してモデルを見る'),
        DeclareLaunchArgument('gamepad', default_value='dualshock4'),
    ]
    input_is = {name: IfCondition(EqualsSubstitution(LaunchConfiguration('input'), name))
                for name in ('gamepad', 'game_client')}
    with_rviz = IfCondition(LaunchConfiguration('rviz'))

    bridge_node = Node(
        package='rabbits_bridge',
        executable='robot_bridge_node',
        name='robot_bridge',
        output='screen',
        parameters=[bridge_config, {'device': LaunchConfiguration('device')}],
    )

    xacro_path = PathJoinSubstitution([
        FindPackageShare('rabbits_description'), 'urdf', 'gamma', 'gamma.xacro'])
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': ParameterValue(
            Command([FindExecutable(name='xacro'), ' ', xacro_path]), value_type=str)}],
        condition=with_rviz,
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('rabbits_bringup'), 'rviz', 'gamma.rviz'])],
        condition=with_rviz,
    )

    gamepad = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(interface_launch, 'gamepad.launch.py')),
        launch_arguments={'gamepad': LaunchConfiguration('gamepad')}.items(),
        condition=input_is['gamepad'],
    )
    game_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(interface_launch, 'game_client.launch.py')),
        condition=input_is['game_client'],
    )

    return LaunchDescription(
        args + [bridge_node, robot_state_publisher, rviz_node, gamepad, game_client])
