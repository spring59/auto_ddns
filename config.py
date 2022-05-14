import os
import configparser


# º”‘ÿ≈‰÷√Œƒº˛
class Config(object):

    def __init__(self, config_file='config.ini'):
        self._path = os.path.join(os.getcwd(), config_file)
        if not os.path.exists(self._path):
            raise FileNotFoundError("No such file: config.ini")
        self._config = configparser.ConfigParser()
        self._config.read(self._path, encoding='utf-8-sig')
        self._configRaw = configparser.RawConfigParser()
        self._configRaw.read(self._path, encoding='utf-8-sig')

    def set_section(self, section):
        if not self._config.has_section(section):
            self._config.add_section(section)

    def set(self, section, option, value=None):
        self._config.set(section, option, value)

    def get(self, section, name):
        return self._config.get(section, name)

    def getRaw(self, section, name):
        return self._configRaw.get(section, name)

    def writer(self):
        self._config.write(open("config.ini", "r+", encoding="utf-8"))

    def writer_all(self):
        self._config.write(open("config.ini", "w", encoding="utf-8"))


global_config = Config()
