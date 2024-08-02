import pickle
import threading
from typing import Any, Dict
from gello.agents.gello_agent import GelloAgent

import numpy as np
import zmq
import torch
from typing import NamedTuple


class ArmState(NamedTuple):
    joint_pos: torch.Tensor
    joint_vel: torch.Tensor
    ee_pos: torch.Tensor
    ee_vel: torch.Tensor


DEFAULT_ROBOT_PORT = 6000

class GelloZMQServer():
    def get_sensors(self):
        pass

    def __init__(
        self,
        hardware_port : int,
        port: int = DEFAULT_ROBOT_PORT,
        host: str = "127.0.0.1",
    ):
        self._agent = GelloAgent(hardware_port)
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        addr = f"tcp://{host}:{port}"
        debug_message = f"Robot Sever Binding to {addr}, Robot: {self._agent}"
        print(debug_message)
        self._timout_message = f"Timeout in Robot Server, Robot: {self._agent}"
        self._socket.bind(addr)
        self._stop_event = threading.Event()

    def serve(self) -> None:
        """Serve the leader robot state over ZMQ."""
        self._socket.setsockopt(zmq.RCVTIMEO, 1000)  # Set timeout to 1000 ms
        while not self._stop_event.is_set():
            try:
                # Wait for next request from client
                message = self._socket.recv()
                request = pickle.loads(message)

                # Call the appropriate method based on the request
                method = request.get("method")
                args = request.get("args", {})
                result: Any
                if method == "get_joint_state":
                    result = ArmState(joint_pos=torch.from_numpy(self._agent._robot.get_joint_state()[:-1]), joint_vel=None, ee_pos=None, ee_vel=None)
                elif method == "get_gripper_state":
                    result = torch.Tensor([self._agent._robot.get_joint_state()[-1]])
                else:
                    result = {"error": "Invalid method"}
                    print(result)
                    raise NotImplementedError(
                        f"Invalid method: {method}, {args, result}"
                    )

                self._socket.send(pickle.dumps(result))
            except zmq.Again:
                print(self._timout_message)
                # Timeout occurred, check if the stop event is set

    def stop(self) -> None:
        """Signal the server to stop serving."""
        self._stop_event.set()