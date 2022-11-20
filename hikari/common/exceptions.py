class BaseError(Exception):
	def __init__(self, ):
		self.err_msg = ""
		self.err_msg_detail = ""


class ButtonNotExistError(BaseError):
	def __init__(self, err_msg):
		self.err_msg = err_msg
		self.err_msg_detail = "123"
		Exception.__init__(self, self.err_msg, self.err_msg_detail)
