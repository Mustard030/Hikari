###############################################################
# 输入命令的执行函数静态类，归纳所有执行命令的函数
###############################################################
import os
import logging

from hikari.common.decorator import function_call_notification
from hikari.config.hikari_config import config


class Command:
    @staticmethod
    def change_paperclip_listening():
        setting = config.listen_paperclip
        setting = not setting
        config.listen_paperclip = setting
        logging.info(f"剪切板监听: {setting}")

    @staticmethod
    def do_nothing():
        pass

    @staticmethod
    @function_call_notification
    def to_mov():
        for root, _, files in os.walk(config["default"]["savePath"]):
            for file in files:
                path = os.path.join(root, file)
                name, ext = os.path.splitext(path)
                if ext in [".mov", ".MOV", ".MP4"]:
                    new_filename = name + ".mp4"
                    os.rename(path, new_filename)
                    logging.info(f"{path} -> {new_filename}")
