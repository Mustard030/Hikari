from enum import Enum, unique


@unique
class DownloadableFileType(Enum):
    Picture = 1
    Video = 2
    ZipFile = 3
    GifFile = 4
