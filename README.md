# Insurance Survey Robot

ROS 2 HumbleとGazebo Fortressを使用した、
被災工場の浸水リスク調査ロボットのシミュレーション。

## 機能
- 設備A、B、Dの自律巡回
- k近傍法による浸水リスク判定
- 浸水リスク検知時の360度旋回
- 出発地点への帰還

## 実行方法

ROS 2 Humble、Gazebo Fortress、
ros_gz_sim、ros_gz_bridge等が必要です。

ワークスペースのsrc内にパッケージを配置後、

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch insurance_survey_robot survey.launch.py
```

※水深・湿度および教師データは模擬データです。
