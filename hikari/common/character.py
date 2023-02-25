import re

from hikari.common.exceptions import LinktypeNotExistError
from hikari.common.linktype import LinkType


class _Character:
	PIXIV = "www.pixiv.net"
	TWITTER = "twitter.com"
	TWIMG = "pbs.twimg.com"
	FANBOX = "fanbox.cc"
	YANDE = "yande.re"
	DANBOORU = "danbooru.donmai.us"
	GELBOORU = "gelbooru.com"
	KEMONO = "www.kemono.party"
	FANTIA = "fantia.jp"
	# https: // danbooru.donmai.us / posts / 5341574
	character_list = [
		PIXIV,
		# TWITTER,
		TWIMG,
		FANBOX,
		YANDE,
		DANBOORU,
		GELBOORU,
		KEMONO,
		FANTIA
	]

	__character_dict = {
		PIXIV: LinkType.PIXIV,
		TWITTER: LinkType.TWITTER,
		TWIMG: LinkType.TWIMG,
		FANBOX: LinkType.FANBOX,
		YANDE: LinkType.YANDE,
		DANBOORU: LinkType.DANBOORU,
		GELBOORU: LinkType.GELBOORU,
		KEMONO: LinkType.KEMONO,
		FANTIA: LinkType.FANTIA,
	}

	pixiv_re_patterns = [
		r"https?://www.pixiv.net/artworks/\d{8,9}",
	]

	kemono_re_patterns = [
		r"https?://www.kemono.party/(?P<platform>\w+)/user/(?P<kemono_userid>\w+)/post/(?P<kemono_postid>\w+)",
	]

	def match(self, value) -> LinkType:
		for c in self.character_list:
			if c in value:
				return self.__character_dict.get(c, None)

		raise LinktypeNotExistError(value)

	def re_match(self, value) -> LinkType:
		pass


Character = _Character()

# res = Character.re_match(r"https://www.pixiv.net/artworks/103041731")

# https://pbs.twimg.com/media/FnjM6XAakAUZR2i?format=jpg&name=large
# g = re.match(r"https?://www.pixiv.net/artworks/(\d{8,9})", "https://www.pixiv.net/artworks/103041731")
# print(g.groups())
