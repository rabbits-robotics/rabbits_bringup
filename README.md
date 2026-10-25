# rabbits_bringup

[![CI](https://github.com/rabbits-robotics/rabbits_bringup/actions/workflows/ci.yml/badge.svg)](https://github.com/rabbits-robotics/rabbits_bringup/actions/workflows/ci.yml)

機体を動かすための横断 launch と rviz 設定。各パッケージ（rabbits_bridge、rabbits_interface、rabbits_description、rabbits_sim）は自分の役割に閉じ、組み合わせはここで持つ。C++ は無く、launch（Python）と設定だけ。

| launch | 内容 |
|---|---|
| `gamma_sim.launch.py` | **実機なし**。偽ファーム（rabbits_sim）→ robot_bridge（device = pty のリンク）→ robot_state_publisher（gamma の URDF）→ rviz。操作は gamepad または game_client。PC 側が作る指令をモデルの関節の動きで確かめる |
| `gamma.launch.py` | **実機**。robot_bridge（実機のシリアル）+ 操作ノード。`rviz:=true` でモデルも見る。sim との違いは device だけ |

```bash
# 偽ファームで（Dev Container 内。ゲームパッドは usbipd で WSL に渡す。rabbits_ws の README 参照）
ros2 launch rabbits_bringup gamma_sim.launch.py                          # gamepad + rviz
ros2 launch rabbits_bringup gamma_sim.launch.py input:=game_client
ros2 launch rabbits_bringup gamma_sim.launch.py rviz:=false input:=none   # 配管だけ。joint_states を echo して確認
ros2 launch rabbits_bringup gamma_sim.launch.py gamepad:=onefun_ps4   # WSL2 + Onefun の PS4 互換機（背面ボタン付き）

# 実機で
ros2 launch rabbits_bringup gamma.launch.py device:=/dev/ttyUSB0
ros2 launch rabbits_bringup gamma.launch.py device:=/dev/ttyTHS1 rviz:=true   # Jetson
```

引数:

| 名前 | 既定 | 意味 |
|---|---|---|
| `input` | `gamepad` | `gamepad`（joy_linux + gamepad_node）/ `game_client` / `none` |
| `rviz` | sim: `true`、実機: `false` | rviz2（実機では robot_state_publisher も）を起動する |
| `link_path`（sim） | `/tmp/gamma_fake` | 偽ファームの pty へのリンク。bridge の `device` に渡す |
| `follow_neck_pitch_roll`（sim） | `false` | 偽ファームが首の Pitch / Roll を指令に追従させる（確認用。実機のファームは機構決定まで送らない） |
| `device`（実機） | `/dev/ttyUSB0` | ファームのシリアル |
| `gamepad` | `dualshock4` | 軸とボタンの番号の組（rabbits_interface の `config/gamepad/<名前>.yaml`。`onefun_ps4` など） |

`gamma_sim.launch.py` は偽ファームがリンクを作るのを待つため、robot_bridge を 1 秒遅らせて起動する。偽ファームを再起動したら launch 全体を再起動する（bridge だけの再起動は可）。

`gamma.repos`: gamma を動かすのに必要なパッケージ一覧（`vcs import src < gamma.repos`）。実機で動いた時点で `vcs export --exact` でコミットを固定する。
