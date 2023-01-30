import json5

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / 'configuration.json'


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

	def get(self, key: str, default=None):
		return self.__config.get(key, default)

	def __update_config(self):
		pass


config = Configuration()
config.load()
