"""
gamma を偽ファーム（rabbits_sim）で動かし、rviz のモデルで指令を確かめる.

偽ファーム → robot_bridge（device = pty のリンク）→ robot_state_publisher → rviz、操作は gamepad か game_client。
実機は gamma.launch.py（device を実機のポートに替えるだけ）。
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
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
    sim_config = os.path.join(
        get_package_share_directory('rabbits_sim'), 'config', 'gamma.yaml')
    interface_launch = os.path.join(
        get_package_share_directory('rabbits_interface'), 'launch')

    args = [
        DeclareLaunchArgument(
            'input', default_value='gamepad',
            description='操作の入力: gamepad | game_client | none'),
        DeclareLaunchArgument(
            'rviz', default_value='true', description='rviz2 を起動する'),
        DeclareLaunchArgument(
            'link_path', default_value='/tmp/gamma_fake',
            description='偽ファームの pty へのシンボリックリンク（robot_bridge の device）'),
        DeclareLaunchArgument(
            'lean_left_button', default_value='-1',
            description='gamepad: リーン左のボタン番号（背面ボタン。-1 = 無し）'),
        DeclareLaunchArgument(
            'lean_right_button', default_value='-1',
            description='gamepad: リーン右のボタン番号（背面ボタン。-1 = 無し）'),
    ]
    input_is = {name: IfCondition(EqualsSubstitution(LaunchConfiguration('input'), name))
                for name in ('gamepad', 'game_client')}

    fake_node = Node(
        package='rabbits_sim',
        executable='gamma_fake_node',
        name='gamma_fake_node',
        output='screen',
        parameters=[sim_config, {'link_path': LaunchConfiguration('link_path')}],
    )

    # 偽ファームがリンクを作ってから bridge を起動する
    bridge_node = TimerAction(
        period=1.0,
        actions=[Node(
            package='rabbits_bridge',
            executable='robot_bridge_node',
            name='robot_bridge',
            output='screen',
            parameters=[bridge_config, {'device': LaunchConfiguration('link_path')}],
        )],
    )

    xacro_path = PathJoinSubstitution([
        FindPackageShare('rabbits_description'), 'urdf', 'gamma', 'gamma.xacro'])
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': ParameterValue(
            Command([FindExecutable(name='xacro'), ' ', xacro_path]), value_type=str)}],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('rabbits_bringup'), 'rviz', 'gamma.rviz'])],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    gamepad = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(interface_launch, 'gamepad.launch.py')),
        launch_arguments={
            'lean_left_button': LaunchConfiguration('lean_left_button'),
            'lean_right_button': LaunchConfiguration('lean_right_button'),
        }.items(),
        condition=input_is['gamepad'],
    )
    game_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(interface_launch, 'game_client.launch.py')),
        condition=input_is['game_client'],
    )

    return LaunchDescription(
        args + [fake_node, bridge_node, robot_state_publisher, rviz_node, gamepad, game_client])
