import logging
import contextlib
import os
import socket
import subprocess
import threading
import time
from typing import Optional, Generator

import cv2
import numpy as np

from src.base import Singleton


logger = logging.getLogger(__name__)

DEFAULT_DISTANCE = 0.25
DEFAULT_SPEED = 10
DEFAULT_DEGREE = 30

# 動画の縦横（処理時間を考慮して３分の1に）
# FRAME_X = int(960/3)
# FRAME_Y = int(720/3)
FRAME_X = 960
FRAME_Y = 720
FRAME_AREA = FRAME_X * FRAME_Y

# ffmpegで必要な情報
FRAME_SIZE = FRAME_AREA * 3
FRAME_CENTER_X = FRAME_X / 2
FRAME_CENTER_Y = FRAME_Y / 2

# ffmpegを使うときのコマンド
CMD_FFMPEG = (f'ffmpeg -hwaccel auto -hwaccel_device opencl -i pipe:0 '
              f'-pix_fmt bgr24 -s {FRAME_X}x{FRAME_Y} -f rawvideo pipe:1')


class DroneManeger(metaclass=Singleton):
    def __init__(
        self,
        host_ip: str = '192.168.10.2',
        host_port: int = 8889,
        drone_ip: str = '192.168.10.1',
        drone_port: int = 8889,
        speed: int = DEFAULT_SPEED,
    ) -> None:
        self.host_ip = host_ip
        self.host_port = host_port
        self.drone_ip = drone_ip
        self.drone_port = drone_port
        self.drone_address = (drone_ip, drone_port)
        self.speed = speed

        # ソケット（IPv4, UDP）
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host_ip, self.host_port))

        # レスポンスを受信するスレッド
        self.response = None
        self.stop_event = threading.Event()
        self._response_thread = threading.Thread(
            target=self.receive_response,
            args=(self.stop_event, )
        )
        self._response_thread.start()

        # FFMPEGのプロセス
        self.proc = subprocess.Popen(
            CMD_FFMPEG.split(' '),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        self.proc_stdin = self.proc.stdin
        self.proc_stdout = self.proc.stdout

        # ビデオを受信するスレッド
        self.video_port = 11111
        self._receive_video_thread = threading.Thread(
            target=self.receive_video,
            args=(
                self.stop_event,
                self.proc_stdin,
                self.host_ip,
                self.video_port
            )
        )
        self._receive_video_thread.start()

        # コマンドを何個も送らないようにする
        self._command_semaphore = threading.Semaphore(1)
        self._command_thread = None

        # ドローンにコマンドを送信する
        self.send_command('command')
        self.send_command('streamon')
        self.set_speed(self.speed)

    def __dell__(self) -> None:
        self.stop()

    def stop(self) -> None:
        """ソケットを閉じる"""
        self.stop_event.set()

        # スレッドが終わるのを待つ
        retry = 0
        while self._response_thread.is_alive():
            time.sleep(0.3)
            if retry > 30:
                break
            retry += 1

        self.socket.close()
        # ffmpegを止める
        os.kill(self.proc.pid, 9)

    def receive_response(self, stop_event: threading.Event) -> None:
        """ドローンからのレスポンスを受信する"""
        while not stop_event.is_set():
            try:
                self.response, ip = self.socket.recvfrom(3000)
                logger.info({
                    'action': 'receive_response',
                    'response': self.response
                })
            except socket.error as ex:
                logger.error({
                    'action': 'receive_response',
                    'exception': ex
                })
                break

    def send_command(self, command: str, blocking: bool = True) -> None:
        """ドローンにコマンドを送信し，レスポンスを受け取る"""
        self._command_thread = threading.Thread(
            target=self._send_command,
            args=(command, blocking, )
        )
        self._command_thread.start()

    def _send_command(self, command: str, blocking: bool = True) -> Optional[str]:
        is_acquire = self._command_semaphore.acquire(blocking=blocking)
        if is_acquire:
            with contextlib.ExitStack() as stack:
                stack.callback(self._command_semaphore.release)

                logger.info({
                    'action': 'sendcommand',
                    'command': command
                })

                # コマンドをエンコードして送信
                self.socket.sendto(
                    command.encode('utf-8'),
                    self.drone_address
                )

                # レスポンスを受信
                retry = 0
                while self.response is None:
                    time.sleep(0.3)
                    if retry > 3:
                        break
                    retry += 1

                if self.response is None:
                    response = None
                else:
                    response = self.response.decode('utf-8')

                return response
        else:
            logger.warning({
                'action': 'send_command',
                'command': command,
                'status': 'not_acquire'
            })

    def takeoff(self):
        """離陸させる"""
        return self.send_command('takeoff')

    def land(self):
        """着陸させる"""
        return self.send_command('land')

    def move(self, direction: str, distance: float):
        """方向と距離を指定して動かす

        Atributes:
            direction: 方向（up, down, left, right, forward, back）
            distance: 距離（0.2~5.0m）
        """
        distance = int(round(distance * 100))
        return self.send_command(f'{direction} {distance}')

    def up(self, distance: int = DEFAULT_DISTANCE):
        """上昇させる"""
        return self.move('up', distance)

    def down(self, distance: int = DEFAULT_DISTANCE):
        """下降させる"""
        return self.move('down', distance)

    def left(self, distance: int = DEFAULT_DISTANCE):
        """左移動させる"""
        return self.move('left', distance)

    def right(self, distance: int = DEFAULT_DISTANCE):
        """右移動させる"""
        return self.move('right', distance)

    def forward(self, distance: int = DEFAULT_DISTANCE):
        """前進させる"""
        return self.move('forward', distance)

    def back(self, distance: int = DEFAULT_DISTANCE):
        """後進させる"""
        return self.move('back', distance)

    def turn(self, direction: str, degree: int):
        """回転させる

        Attributes:
            direction: 回転方向（cw: 時計回り, ccw: 反時計回り）
            degree: 角度（1~360°）
        """
        return self.send_command(f'{direction} {degree}')

    def turn_left(self, degree: int = DEFAULT_DEGREE):
        """反時計回りに回転させる"""
        return self.turn('ccw', degree)

    def turn_right(self, degree: int = DEFAULT_DEGREE):
        """時計回りに回転させる"""
        return self.turn('cw', degree)

    def set_speed(self, speed: int):
        """速度を設定する

        Attributes:
            speed: 速度（10~100cm/s）
        """
        return self.send_command(f'speed {speed}')

    def receive_video(
        self,
        stop_event: threading.Event,
        pipe_in,
        host_ip: str,
        video_port: int,
    ):
        """ソケットをつないで，動画を受けとる

        Arguments:
            stop_envent:
            pipe_in:
            host_ip: ホストのIPアドレス
            video_port: 動画用のポート
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_video:
            sock_video.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )
            sock_video.settimeout(0.5)
            sock_video.bind((host_ip, video_port))
            data = bytearray(2048)

            while not stop_event.is_set():
                # ソケットから取ってきたデータを格納
                try:
                    size, addr = sock_video.recvfrom_into(data)
                    # logger.info({
                    #     'action': 'receive_video',
                    #     'data': data,
                    # })
                except socket.timeout as ex:
                    logging.warning({
                        'action': 'receive_video',
                        'exception': ex,
                    })
                    time.sleep(0.5)
                    continue
                except socket.error as ex:
                    logger.error({
                        'action': 'receive_video',
                        'exception': ex
                    })

                # 受け取ったときに返ってきたデータをパイプに流す
                try:
                    pipe_in.write(data[:size])
                    pipe_in.flush()
                except Exception as ex:
                    logger.error({
                        'action': 'receive_video',
                        'exception': ex
                    })
                    break

    def video_binary_generator(self) -> Generator[np.ndarray, None, None]:
        while True:
            try:
                frame = self.proc_stdout.read(FRAME_SIZE)
            except Exception as ex:
                logger.error({
                    'action': 'video_binary_generator',
                    'exception': ex,
                })
                continue

            if not frame:
                continue

            frame = np.fromstring(
                frame,
                np.uint8
            ).reshape(FRAME_Y, FRAME_X, 3)

            yield frame

    def video_jpeg_generator(self):
        for frame in self.video_binary_generator():
            _, jpeg = cv2.imencode('.jpg', frame)
            jpeg_binary = jpeg.tobytes()

            yield jpeg_binary
