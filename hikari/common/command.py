###############################################################
# 输入命令的执行函数静态类，归纳所有执行命令的函数
###############################################################
import logging

from hikari.config.hikari_config import config


class Command:
    @staticmethod
    def changePaperclipListening():
        setting = config.listen_paperclip
        setting = not setting
        config.listen_paperclip = setting
        logging.info(f"剪切板监听: {setting}")

    @staticmethod
    def doNothing():
        pass
