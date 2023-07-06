from pathlib import Path

import json5

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / 'configuration.json'


class _SubOption:
    def __init__(self, data: dict):
        self.__options = {}
        for key in data:
            if isinstance(data[key], dict):
                self.__options[key] = _SubOption(data[key])
            else:
                self.__options[key] = data[key]

    def __getitem__(self, item):
        return self.__options[item]

    def __setitem__(self, key, value):
        if isinstance(self.__options[key], _SubOption):
            raise TypeError('Can`t change a option')
        self.__options[key] = value

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        res = {}
        for key in self.__options:
            if isinstance(self.__options[key], _SubOption):
                res[key] = self.__options[key].to_dict()
            else:
                res[key] = self.__options[key]
        return res


class Configuration:
    def __init__(self, path=DEFAULT_CONFIG_PATH):
        self.__options = None
        self.__path: str | Path = path

    def __getitem__(self, item):
        return self.__options[item]

    def __setitem__(self, key, value):
        if isinstance(self.__options[key], _SubOption):
            raise TypeError('Can`t change a option')
        self.__options[key] = value

    def __str__(self):
        return str(self.__options.to_dict())

    def load(self):
        with open(self.__path, encoding='utf-8') as config_file:
            data = json5.load(config_file)
            self.__options = _SubOption(data)

    def save(self):
        with open(self.__path, 'w', encoding='utf-8') as config_file:
            json5.dump(self.__options.to_dict(), config_file, ensure_ascii=False, indent=2)

    @property
    def listen_paperclip(self):
        return self['setting']['enablePaperclipListening']

    @listen_paperclip.setter
    def listen_paperclip(self, value):
        self['setting']['enablePaperclipListening'] = value


# class __Configuration:
#     def __init__(self, path=DEFAULT_CONFIG_PATH):
#         self.__config: dict = {}
#         self.__path: str | Path = path
#
#     @property
#     def listen_paperclip(self):
#         return self.__config.get('setting').get('enablePaperclipListening', False)
#
#     @listen_paperclip.setter
#     def listen_paperclip(self, value):
#         self.__config['setting']['enablePaperclipListening'] = value
#
#     def load(self):
#         with open(self.__path, encoding='utf-8') as config_file:
#             self.__config = json5.load(config_file)
#
#     def save(self):
#         with open(self.__path, 'w', encoding='utf-8') as config_file:
#             json5.dump(self.__config, config_file, ensure_ascii=False, indent=2)
#
#     def get(self, key: str, default=None) -> dict:
#         return self.__config.get(key, default)
#
#     def __update_config(self):
#         pass


config = Configuration()
config.load()
