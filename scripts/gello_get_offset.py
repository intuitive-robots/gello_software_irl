from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import tyro

from gello.dynamixel.driver import DynamixelDriver
from gello.agents.gello_agent import DynamixelRobotConfig, store_config

MENAGERIE_ROOT: Path = Path(__file__).parent / "third_party" / "mujoco_menagerie"


@dataclass
class Args:
    port: str = "/dev/ttyUSB0"
    """The port that GELLO is connected to."""

    start_joints: Tuple[float, ...] = (0, 0, 0, 0, 0, 0)
    """The joint angles that the GELLO is placed in at (in radians)."""

    joint_signs: Tuple[float, ...] = (1, 1, -1, 1, 1, 1)
    """The joint angles that the GELLO is placed in at (in radians)."""

    gripper: bool = True
    """Whether or not the gripper is attached."""

    def __post_init__(self):
        assert len(self.joint_signs) == len(self.start_joints)
        for idx, j in enumerate(self.joint_signs):
            assert (
                j == -1 or j == 1
            ), f"Joint idx: {idx} should be -1 or 1, but got {j}."

    @property
    def num_robot_joints(self) -> int:
        return len(self.start_joints)

    @property
    def num_joints(self) -> int:
        extra_joints = 1 if self.gripper else 0
        return self.num_robot_joints + extra_joints


def get_config(args: Args) -> None:

    joint_ids = list(range(1, args.num_joints + 1))
    driver = DynamixelDriver(joint_ids, port=args.port, baudrate=57600)

    # Warmup
    for _ in range(10):
        driver.get_joints()

    # Determine configuration
    curr_joints = driver.get_joints()[:args.num_robot_joints]
    start_joints = np.array(args.start_joints)
    joint_signs = np.array(args.joint_signs)
    precise_offsets = curr_joints - joint_signs * start_joints
    pi_offset = np.round(precise_offsets / (np.pi / 2)).astype(int)
    print(f"Current joint position: {curr_joints}")
    print(f"Precise offsets                   : {[f'{x:.3f}' for x in precise_offsets]}".replace("'", ""))
    print(f"Closest offsets as multiple of pi : {[f'{x}*np.pi/2' for x in pi_offset]}".replace("'", ""))
    if args.gripper:
        gripper_open = np.rad2deg(driver.get_joints()[-1]) - 0.2
        gripper_closed = np.rad2deg(driver.get_joints()[-1]) - 42
        print(f"Gripper open (degrees)       : {gripper_open}")
        print(f"Gripper closed (degrees)     : {gripper_closed}")
        gripper_config = (args.num_joints, int(gripper_open), int(gripper_closed))
    else:
        gripper_config = None

    # Store configuration
    store = input("Do you want to store the configuration? (y|n)\n")
    if store.lower() == "y" or store.lower() == "yes":
        config = DynamixelRobotConfig(
            joint_ids = tuple(range(1, args.num_robot_joints + 1)),
            joint_offsets = tuple(precise_offsets.tolist()),
            joint_signs = tuple(map(int, args.joint_signs)),
            gripper_config = gripper_config,
        )
        store_config(config=config, port=args.port)
        print("The configuration was stored successfully")
    else:
        print("The configuration was not stored")


def main(args: Args) -> None:
    get_config(args)


if __name__ == "__main__":
    main(tyro.cli(Args))
