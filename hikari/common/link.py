from .picture import Picture


class LinkType:
	PIXIV = "pixiv"
	TWITTER = "twitter"
	FANBOX = "fanbox"
	YANDE = "yande"
	KEMONO = "kemono"
	FANTIA = "fantia"


class _Character:
	PIXIV = "www.pixiv.net"
	TWITTER = "twitter.com"
	FANBOX = "fanbox.cc"
	YANDE = "yande.re"
	KEMONO = "www.kemono.party"
	FANTIA = "fantia.jp"

	character_list = [PIXIV, TWITTER, FANBOX, YANDE, KEMONO, FANTIA]

	_character_dict = {
		PIXIV: LinkType.PIXIV,
		TWITTER: LinkType.TWITTER,
		FANBOX: LinkType.FANBOX,
		YANDE: LinkType.YANDE,
		KEMONO: LinkType.KEMONO,
		FANTIA: LinkType.FANTIA,
	}

	def match(self, value) -> LinkType:
		for c in self.character_list:
			if c in value:
				return self._character_dict.get(c)

	def __contains__(self, item):
		for c in self.character_list:
			if c in item:
				return True

		return False


Character = _Character()


class Link:
	def __init__(self, url):
		self.url = url
		self.linktype = Character.match(url)

	async def fetch(self):
		pass
