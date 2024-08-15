from dataclasses import dataclass
import threading
import tyro

from gello.zmq_core.gello_server import GelloZMQServer

@dataclass
class Args:
    mode: str = "unimanual"
    hardware_port: str = "/dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_FT94ER3L-if00-port0"
    hardware_port_left: str = "/dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_FT94ER3L-if00-port0"
    hardware_port_right: str = "/dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_FT94EVRT-if00-port0"
    host: str = "127.0.0.1"
    server_port: int = 6000
    server_port_left = 6000
    server_port_right = 6001


def launch_robot_server(args: Args):
    if args.mode == "unimanual":

        server = GelloZMQServer(
            hardware_port = args.hardware_port,
            port = args.server_port,
            host = args.host
        )
        print(f"Started server for {args.hardware_port} on {args.host}:{args.server_port_right}")
        server.serve()
    elif args.mode == "bimanual":

        server_left = GelloZMQServer(
            hardware_port = args.hardware_port_left,
            port = args.server_port_left,
            host = args.host
        )

        server_right = GelloZMQServer(
            hardware_port= args.hardware_port_right,
            port = args.server_port_right,
            host = args.host
        )
        
        server_left_thread = threading.Thread(target=server_left.serve)
        server_right_thread = threading.Thread(target=server_right.serve)

        server_left_thread.start()
        print(f"Started server for left {args.hardware_port_left} on {args.host}:{args.server_port_left}")
        server_right_thread.start()
        print(f"Started server for right {args.hardware_port_right} on {args.host}:{args.server_port_right}")

        server_left_thread.join()
        server_right_thread.join()

    else:
        raise NotImplementedError(
            f"Mode {args.mode} not implemented" + "!"
        )

def main(args):
    launch_robot_server(args)


if __name__ == "__main__":
    main(tyro.cli(Args))
