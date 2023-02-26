import json5

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / 'configuration.json'


class _SubOption:
	def __init__(self, data: dict):
		self.options = {}
		for key in data:
			if isinstance(data[key], dict):
				self.options[key] = _SubOption(data[key])
			else:
				self.options[key] = data[key]

	def __getitem__(self, item):
		return self.options[item]

	# def __setattr__(self, key, value):
	# 	self.options[key] = value

	def __getattribute__(self, item):
		return super().__getattribute__(item)

	def to_dict(self):
		res = {}
		for key in self.options:
			if isinstance(self.options[key], _SubOption):
				res[key] = self.options[key].to_dict()
			else:
				res[key] = self.options[key]
		return res


class TestConfig:
	def __init__(self, path=DEFAULT_CONFIG_PATH):
		self.options = None
		self.__path: str | Path = path

	def __getitem__(self, item):
		return self.options[item]

	def load(self):
		with open(self.__path, encoding='utf-8') as config_file:
			data = json5.load(config_file)
			self.options = _SubOption(data)


class Configuration:
	def __init__(self, path=DEFAULT_CONFIG_PATH):
		self.__config: dict = {}
		self.__path: str | Path = path

	@property
	def listen_paperclip(self):
		return self.__config.get('setting').get('enablePaperclipListening', False)

	@listen_paperclip.setter
	def listen_paperclip(self, value):
		self.__config['setting']['enablePaperclipListening'] = value

	def load(self):
		with open(self.__path, encoding='utf-8') as config_file:
			self.__config = json5.load(config_file)

	def save(self):
		with open(self.__path, 'w', encoding='utf-8') as config_file:
			json5.dump(self.__config, config_file, ensure_ascii=False, indent=2)

	def get(self, key: str, default=None) -> dict:
		return self.__config.get(key, default)

	def __update_config(self):
		pass


config = Configuration()
config.load()

# config = TestConfig()
# config.load()
# config.__dict__['b'] = 3
# print(config.b)
# print(dir(config))
