from dataclasses import dataclass, asdict
import json
from typing import Dict, Optional, Sequence, Tuple
from pathlib import Path

import numpy as np

from gello.agents.agent import Agent
from gello.robots.dynamixel import DynamixelRobot


CONFIG_FOLDER_PATH = Path(__file__).parent.parent.parent / "configurations"

@dataclass
class DynamixelRobotConfig:
    joint_ids: Sequence[int]
    """The joint ids of GELLO (not including the gripper). Usually (1, 2, 3 ...)."""

    joint_offsets: Sequence[float]
    """The joint offsets of GELLO. There needs to be a joint offset for each joint_id and should be a multiple of pi/2."""

    joint_signs: Sequence[int]
    """The joint signs of GELLO. There needs to be a joint sign for each joint_id and should be either 1 or -1.

    This will be different for each arm design. Reference the examples below for the correct signs for your robot.
    """

    gripper_config: Tuple[int, int, int]
    """The gripper config of GELLO. This is a tuple of (gripper_joint_id, degrees in open_position, degrees in closed_position)."""

    def __post_init__(self):
        assert len(self.joint_ids) == len(self.joint_offsets)
        assert len(self.joint_ids) == len(self.joint_signs)

    def make_robot(
        self, port: str = "/dev/ttyUSB0", start_joints: Optional[np.ndarray] = None
    ) -> DynamixelRobot:
        return DynamixelRobot(
            joint_ids=self.joint_ids,
            joint_offsets=list(self.joint_offsets),
            real=True,
            joint_signs=list(self.joint_signs),
            port=port,
            gripper_config=self.gripper_config,
            start_joints=start_joints,
        )

def store_config(config: DynamixelRobotConfig, port: str, config_folder_path: str = CONFIG_FOLDER_PATH) -> None:
    json_data =  json.dumps(asdict(config), indent=4)
    path = Path(config_folder_path) / (Path(port).name + ".json")
    path.parent.mkdir(parents=False, exist_ok=True)
    with path.open(mode="w") as json_file:
        json_file.write(json_data)

def load_config(port: str, config_folder_path: str = CONFIG_FOLDER_PATH) -> DynamixelRobotConfig:
    path = Path(config_folder_path) / (Path(port).name + ".json")
    assert path.exists()
    with path.open(mode="r") as json_file:
        json_data = json.load(json_file)
    return DynamixelRobotConfig(**json_data)

class GelloAgent(Agent):
    def __init__(
        self,
        port: str,
        dynamixel_config: Optional[DynamixelRobotConfig] = None,
        start_joints: Optional[np.ndarray] = None,
    ):
        if dynamixel_config is not None:
            self._robot = dynamixel_config.make_robot(
                port=port, start_joints=start_joints
            )
        else:
            assert Path(port).exists(), port

            config = load_config(port)
            self._robot = config.make_robot(port=port, start_joints=start_joints)

    def act(self, obs: Dict[str, np.ndarray]) -> np.ndarray:
        return self._robot.get_joint_state()
        dyna_joints = self._robot.get_joint_state()
        # current_q = dyna_joints[:-1]  # last one dim is the gripper
        current_gripper = dyna_joints[-1]  # last one dim is the gripper

        print(current_gripper)
        if current_gripper < 0.2:
            self._robot.set_torque_mode(False)
            return obs["joint_positions"]
        else:
            self._robot.set_torque_mode(False)
            return dyna_joints


if __name__ == "__main__":

    # Test storing a configuration

    config = DynamixelRobotConfig(
        joint_ids=(1, 2, 3, 4, 5, 6, 7),
        joint_offsets=(4.595, 3.124, 4.550, 1.323, 3.336, 1.147, 5.165),
        joint_signs=(1, -1, 1, -1, 1, 1, 1),
        gripper_config=(8, 198, 148),
    )
    store_config(
        config=config,
        port="/dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_TEST-if00-port0",
    )

    # Test loading a configuration

    loaded_config = load_config(port="/dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_TEST-if00-port0")
    print(loaded_config)
