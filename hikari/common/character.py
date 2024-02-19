import re
from typing import Type

from hikari.common import content
from hikari.common.exceptions import LinktypeNotSupportError
from hikari.common.linktype import LinkType


# 基类
class BaseMetaMatchingStrategy(type):
    record_cls = []

    def __new__(mcs, name, bases, attrs):
        new_cls = type.__new__(mcs, name, bases, attrs)
        # 如果子类名为Base，不会注册
        if name not in ["BaseMatchingStrategy"]:
            BaseMetaMatchingStrategy.record_cls.append(new_cls)
        return new_cls


class BaseMatchingStrategy(object, metaclass=BaseMetaMatchingStrategy):
    linktype = LinkType.NONE

    @classmethod
    def is_match(cls, url) -> re.Match:
        """
        是否匹配该类链接的格式
        """
        ...

    @classmethod
    def get_content(cls, url) -> content.Content:
        """
        若匹配该类型的链接格式，则返回Content类的具体子类
        """
        ...


# 策略类
class TwimgMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.TWIMG

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https?://pbs.twimg.com/media/(.*?)"
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Twimg(url)


class PixivMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.PIXIV

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https?://www.pixiv.net/artworks/(\d{8,9})",
            r"https?://www.pixiv.net/member_illust.php\?mode=\w+&illust_id=(\d{8,9})",
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Pixiv(url)


class KemonoMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.KEMONO

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https://(www.)?kemono.(party|su)/\w+/user/(\d+)/post/(\d+)"
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Kemono(url)


class YandeMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.YANDE

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https?://yande.re/post/show/\d+",
            r"https?://yande.re/post/browse#\d+",
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Yande(url)


class GelbooruMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.GELBOORU

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https?://gelbooru.com/index.php\?page=post&s=view&id=\d+",
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Gelbooru(url)


class SankakuMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.SANKAKU

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https?://beta.sankakucomplex.com/zh-CN/post/show/(\d+)",
            r"https?://sankaku.app/post/show/(\d+)"
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Sankaku(url)


class DanbooruMatchingStrategy(BaseMatchingStrategy):
    linktype = LinkType.DANBOORU

    @classmethod
    def is_match(cls, url) -> re.Match:
        patterns = [
            r"https://danbooru.donmai.us/posts/(\d+)\?q=parent%3A(\d+)",
            r"https://danbooru.donmai.us/posts/(\d+)",
        ]
        for pattern in patterns:
            if res := re.match(pattern, url):
                return res

    @classmethod
    def get_content(cls, url):
        return content.Danbooru(url)


def match_strategy(url) -> Type[BaseMatchingStrategy]:
    for cls in BaseMetaMatchingStrategy.record_cls:
        if cls.is_match(url):
            return cls

    raise LinktypeNotSupportError(url)

# urls = r'https://beta.sankakucomplex.com/zh-CN/post/show/16579876?tags=parent%3A7323385'
# c = match_strategy(urls)
# print(c.get_content(urls))
