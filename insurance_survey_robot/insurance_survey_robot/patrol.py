import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import String

from .risk_ai import predict

# Gazeboの設備の近くに設定した巡回地点 (名前, X座標, Y座標)
A = ('A: power supply', 1.5, 0.0)
B = ('B: drainage pump', 1.5, 1.5)
D = ('D: electrical panel', 0.0, 1.5)
HOME = ('HOME', 0.0, 0.0)

# AI判定用の架空データ (水深cm, 湿度%)
FLOOD_SCENARIO = {
    'A': (1, 52),      # 正常：回転しない
    'B': (18, 90),     # 浸水リスク：360度回転
    'D': (15, 88),     # 浸水リスク：360度回転
}
NORMAL_SCENARIO = {key: (1, 52) for key in ('A', 'B', 'D')}


class Patrol(Node):
    def __init__(self):
        super().__init__('insurance_patrol')
        self.declare_parameter('scenario', 'flood')
        scenario = self.get_parameter('scenario').value
        if scenario not in ('flood', 'normal'):
            raise ValueError('scenario must be flood or normal')
        self.readings = FLOOD_SCENARIO if scenario == 'flood' else NORMAL_SCENARIO

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/survey/status', 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_timer(0.1, self.step)

        self.pose = None
        self.goals = [A, B, D, HOME]
        self.index = 0
        self.results = {}
        self.done = False
        self.pause_until = 0.0
        self.announced_wait = False

        # 360度回転用の状態（角度は /odom から計算する）
        self.turning = False
        self.turn_machine = ''
        self.turn_last_yaw = 0.0
        self.turned_angle = 0.0
        self.turn_started_at = 0.0
        self.announce('START: inspect A, B and D; then return HOME')

    def announce(self, message):
        self.get_logger().info(message)
        self.status_pub.publish(String(data=message))

    def on_odom(self, odom):
        p = odom.pose.pose.position
        q = odom.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        if self.turning:
            # -πと+πの境界を越えても、回転した角度を正しく積算する
            delta = math.atan2(math.sin(yaw - self.turn_last_yaw),
                               math.cos(yaw - self.turn_last_yaw))
            self.turned_angle += delta
            self.turn_last_yaw = yaw
        self.pose = (p.x, p.y, yaw)

    def stop(self):
        self.cmd_pub.publish(Twist())

    def arrive(self, name):
        self.stop()
        self.announce(f'ARRIVED: {name} (actual x={self.pose[0]:.2f}, y={self.pose[1]:.2f})')
        machine = name.split(':')[0]
        if machine in self.readings:
            water, humidity = self.readings[machine]
            result = predict(water, humidity)
            self.results[machine] = result
            self.announce(
                f'AI RESULT {machine}: water={water}cm humidity={humidity}% -> {result}'
            )
            if result == 'FLOOD_RISK':
                # 異常のある設備では、その場で追加確認の動作を模擬する
                self.turning = True
                self.turn_machine = machine
                self.turned_angle = 0.0
                self.turn_last_yaw = self.pose[2]
                self.turn_started_at = 0.0
                self.announce(f'EXTRA CHECK {machine}: ROTATE 360 START')
        else:
            summary = ' | '.join(f'{key}={self.results[key]}' for key in ('A', 'B', 'D'))
            self.announce(f'SUMMARY: {summary}')
            self.announce('FINISHED: results ready for human inspection')
            self.done = True

        self.index += 1
        self.pause_until = time.monotonic() + 2.0

    def step(self):
        if self.done:
            self.stop()
            return
        if self.pose is None:
            if not self.announced_wait:
                self.get_logger().info('Waiting for /odom (start Gazebo and bridge)')
                self.announced_wait = True
            return
        if time.monotonic() < self.pause_until:
            self.stop()
            return

        if self.turning:
            if self.turned_angle >= 2 * math.pi - 0.06:
                self.stop()
                self.announce(f'EXTRA CHECK {self.turn_machine}: ROTATE 360 COMPLETE')
                self.turning = False
                self.pause_until = time.monotonic() + 1.0
                return
            if not self.turn_started_at:
                self.turn_started_at = time.monotonic()
            if time.monotonic() - self.turn_started_at > 25.0:
                # 車輪が動かない場合に、いつまでも回転指令を出し続けない
                self.stop()
                self.announce(f'WARNING: rotation timed out at {self.turn_machine}')
                self.turning = False
                return
            cmd = Twist()
            cmd.angular.z = 0.5  # その場でゆっくり左回転（約13秒/周）
            self.cmd_pub.publish(cmd)
            return

        name, goal_x, goal_y = self.goals[self.index]
        x, y, yaw = self.pose
        dx, dy = goal_x - x, goal_y - y
        distance = math.hypot(dx, dy)
        if distance < 0.14:
            self.arrive(name)
            return

        target_angle = math.atan2(dy, dx)
        error = math.atan2(math.sin(target_angle - yaw),
                           math.cos(target_angle - yaw))
        cmd = Twist()
        cmd.angular.z = max(-0.75, min(0.75, 1.6 * error))
        if abs(error) < 0.3:
            cmd.linear.x = min(0.28, 0.55 * distance)
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = Patrol()
    try:
        rclpy.spin(node)
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
