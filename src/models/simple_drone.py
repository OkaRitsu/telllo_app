from typing import Dict, Union

import numpy as np

from src.models.base_drone import BaseDrone


class SimpleDrone(BaseDrone):
    def __init__(
        self,
        host_ip: str = "192.168.10.2",
        host_port: int = 8889,
        drone_ip: str = "192.168.10.1",
        drone_port: int = 8889,
        speed: int = 10,
    ) -> None:
        super().__init__(host_ip, host_port, drone_ip, drone_port, speed)

        self.action_status = 0

    def act(self, observations: Dict[str, Union[float, np.array]]) -> None:
        """左右の回転を繰り返す"""
        if self.action_status % 2 == 0:
            response = self.turn_left()
        else:
            response = self.turn_right()

        # レスポンスが返って来ていればカウンターを増やす
        if response is not None:
            self.action_status += 1
