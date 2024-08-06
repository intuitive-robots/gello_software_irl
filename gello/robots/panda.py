import time
from typing import Dict

import numpy as np

from gello.robots.robot import Robot

MAX_OPEN = 0.09

RESPOSE = [0.2719, -0.5165, 0.2650, -1.6160, -0.0920, 1.6146, -1.9760] # Normal reset pose for kitchen robot

class PandaRobot(Robot):
    """A class representing a UR robot."""

    def __init__(self, robot_ip: str = "100.97.47.74", robot_port: int = 50051, gripper_port: int = 50052, reset_pose = RESPOSE):
        from real_robot.real_robot_env.robot.hardware_franka import FrankaArm, ControlType
        from real_robot.real_robot_env.robot.hardware_frankahand import FrankaHand

        robot_arm = FrankaArm(
            name=f"Franka arm",
            ip_address=robot_ip,
            port=robot_port,
            control_type=ControlType.IMITATION_CONTROL,
            default_reset_pose=reset_pose,
        )
        assert robot_arm.connect(), f"Connection to {robot_arm.name} failed"
        robot_arm.reset()

        robot_gripper = FrankaHand(
            name=f"Franka gripper", ip_address=robot_ip, port=gripper_port
        )
        assert robot_gripper.connect(), f"Connection to {robot_gripper.name} failed"

        self.robot = robot_arm
        self.gripper = robot_gripper

    def num_dofs(self) -> int:
        """Get the number of joints of the robot.

        Returns:
            int: The number of joints of the robot.
        """
        return 8

    def get_joint_state(self) -> np.ndarray:
        """Get the current state of the leader robot.

        Returns:
            T: The current state of the leader robot.
        """
        robot_joints = self.robot.get_state().joint_pos
        gripper_pos = self.gripper.get_sensors()[0]
        pos = np.append(robot_joints, gripper_pos / MAX_OPEN)
        return pos

    def command_joint_state(self, joint_state: np.ndarray) -> None:
        """Command the leader robot to a given state.

        Args:
            joint_state (np.ndarray): The state to command the leader robot to.
        """
        import torch

        self.robot.apply_commands(q_desired=torch.tensor(joint_state[:-1]))

        if joint_state[-1] > 0.5:
            gripper_command = -1
        else:
            gripper_command = 1
        self.gripper.apply_commands(gripper_command) # goto(width=(MAX_OPEN * (1 - joint_state[-1])), speed=1, force=1)

    def get_observations(self) -> Dict[str, np.ndarray]:
        joints = self.get_joint_state()
        pos_quat = np.zeros(7)
        gripper_pos = np.array([joints[-1]])
        return {
            "joint_positions": joints,
            "joint_velocities": joints,
            "ee_pos_quat": pos_quat,
            "gripper_position": gripper_pos,
        }


def main():
    robot = PandaRobot()
    current_joints = robot.get_joint_state()
    # move a small delta 0.1 rad
    move_joints = current_joints + 0.05
    # make last joint (gripper) closed
    move_joints[-1] = 0.5
    time.sleep(1)
    m = 0.09
    robot.gripper.goto(1 * m, speed=255, force=255)
    time.sleep(1)
    robot.gripper.goto(1.05 * m, speed=255, force=255)
    time.sleep(1)
    robot.gripper.goto(1.1 * m, speed=255, force=255)
    time.sleep(1)


if __name__ == "__main__":
    main()
