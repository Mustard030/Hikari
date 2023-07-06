from pyppeteer import launch

from .const import DEFAULT_USER_AGENT


# Page类用于pyppeteer打开页面等基本设置和操作
#
#
class Page:
	def __init__(self, headless):
		self.browser = None
		self.page = None
		self.headless = bool(headless)

	async def __aenter__(self):
		self.browser = await launch(headless=self.headless, args=['--disable-infobars'])
		self.page = await self.browser.newPage()
		await self.page.setUserAgent(DEFAULT_USER_AGENT)
		await self.page.evaluate("""
								    () =>{
								        Object.defineProperties(navigator,{
								            webdriver:{
								            get: () => false
								            }
								        })
								    }
								""")
		await self.page.setViewport(viewport={'width': 931, 'height': 974})
		await self.page.setJavaScriptEnabled(True)

		return self.page

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.browser.close()


class TwitterPage(Page):
	def __init__(self, headless):
		super().__init__(headless)

	async def set_cookies(self, cookies: dict = None, domain: str = ""):
		if cookies:
			[await self.page.setCookie({'name': k, 'value': v, 'domain': domain}) for k, v in cookies.items()]

	async def parse_content(self):
		pass
