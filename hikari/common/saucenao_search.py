import asyncio
import io
import logging
import os

import aiohttp
from PIL import Image

from hikari.common.decorator import retry
from hikari.common.exceptions import ImageIOError, PathNotExistError
from hikari.common.function import proxy_path
from hikari.common.link import Link
from hikari.config.hikari_config import config

index_hmags = '0'
index_reserved = '0'
index_hcg = '0'
index_ddbobjects = '0'
index_ddbsamples = '0'
index_pixiv = '1'
index_pixivhistorical = '1'
index_reserved = '0'
index_seigaillust = '1'
index_danbooru = '1'
index_drawr = '1'
index_nijie = '1'
index_yandere = '1'
index_animeop = '0'
index_reserved = '0'
index_shutterstock = '0'
index_fakku = '0'
index_hmisc = '0'
index_2dmarket = '0'
index_medibang = '0'
index_anime = '0'
index_hanime = '0'
index_movies = '0'
index_shows = '0'
index_gelbooru = '0'
index_konachan = '0'
index_sankaku = '0'
index_animepictures = '0'
index_e621 = '0'
index_idolcomplex = '0'
index_bcyillust = '0'
index_bcycosplay = '0'
index_portalgraphics = '0'
index_da = '0'
index_pawoo = '0'
index_madokami = '0'
index_mangadex = '0'

db_bitmask = str(
		int(index_mangadex + index_madokami + index_pawoo + index_da + index_portalgraphics + index_bcycosplay + index_bcyillust + index_idolcomplex + index_e621 + index_animepictures + index_sankaku + index_konachan + index_gelbooru + index_shows + index_movies + index_hanime + index_anime + index_medibang + index_2dmarket + index_hmisc + index_fakku + index_shutterstock + index_reserved + index_animeop + index_yandere + index_nijie + index_drawr + index_danbooru + index_seigaillust + index_anime + index_pixivhistorical + index_pixiv + index_ddbsamples + index_ddbobjects + index_hcg + index_hanime + index_hmags,
		    2
		    )
)


class Saucenao:
	def __init__(self, path, minsim=60):
		"""
		:param path: 本地图片路径
		:param minsim: 搜索结果最小相似度值（小于此相似度的结果将被舍弃）
		"""
		self.path = os.path.normpath(path)
		self.minsim = minsim
		self.__api_key = config["apikey"]["saucenao"]
		self.proxy_path = proxy_path()

	@retry(2)
	async def search(self) -> list[Link]:
		if not os.path.exists(self.path):
			raise PathNotExistError(self.path)
		try:
			image = Image.open(self.path).convert('RGB')
		except OSError:
			# logging.warning(f"图片损坏{self.path}")
			raise ImageIOError(self.path)
		else:
			image_data = io.BytesIO()
			image.save(image_data, format='PNG')

		url = f'http://saucenao.com/search.php?output_type=2&numres=5&minsim={self.minsim}&dbmask={db_bitmask}&api_key={self.__api_key}'
		files = {'file': image_data.getvalue()}
		image_data.close()

		async with aiohttp.ClientSession() as session:
			async with session.post(url, data=files, proxy=self.proxy_path) as resp:
				if resp.status != 200:
					if resp.status == 403:
						pass
					data = await resp.json()



# s = Saucenao(r"C:\Users\Administrator\Downloads\Moisture\72751229_p0.png")
# asyncio.run(s.search())
