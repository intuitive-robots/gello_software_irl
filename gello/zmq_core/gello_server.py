import pickle
import threading
import itertools
from typing import Any, Optional
from gello.agents.gello_agent import GelloAgent

import zmq
import torch
from typing import NamedTuple


class ArmState(NamedTuple):
    joint_pos: Optional[torch.Tensor]
    joint_vel: Optional[torch.Tensor]
    ee_pos: Optional[torch.Tensor]
    ee_vel: Optional[torch.Tensor]


DEFAULT_GELLO_PORT = 6000

class GelloZMQServer():
    def get_sensors(self):
        pass

    def __init__(
        self,
        hardware_port : str,
        port: int = DEFAULT_GELLO_PORT,
        host: str = "127.0.0.1",
    ):
        self._agent = GelloAgent(hardware_port)
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        addr = f"tcp://{host}:{port}"
        self._timout_message = f"Timeout in Robot Server, Robot: {self._agent}"
        self._running_message = f"Successfully running Robot Server, Robot: {self._agent}"
        self._spinner = itertools.cycle(["-", "\\", "|", "/"])
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

                # Print server status
                self.__print_running()

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
                    raise NotImplementedError(
                        f"Invalid method: {method}, {args, result}"
                    )

                self._socket.send(pickle.dumps(result))
            except zmq.Again:
                self.__print_timout()
                # Timeout occurred, check if the stop event is set

    def stop(self) -> None:
        """Signal the server to stop serving."""
        self._stop_event.set()

    def __print_timout(self) -> None:
        print(f"\r{self._timout_message} [{next(self._spinner)}]{' '*20}", end="", flush=True)

    def __print_running(self) -> None:
        print(f"\r{self._running_message}{' '*20}", end="", flush=True)
