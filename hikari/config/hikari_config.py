import json5

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / 'configuration.json'


class Configuration:
	def __init__(self):
		self._config = None

	def load(self, config_path: str = DEFAULT_CONFIG_PATH):
		with open(config_path, encoding='utf-8') as config_file:
			self._config = json5.load(config_file)

	def get(self, key: str, default=None):
		return self._config.get(key, default)

	def __update_config(self):
		pass


config = Configuration()
config.load()
