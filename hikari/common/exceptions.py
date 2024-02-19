class BaseError(Exception):
    def __init__(self, err_msg, err_msg_detail):
        self.err_msg = err_msg
        self.err_msg_detail = err_msg_detail

    def __str__(self):
        if len(self.err_msg_detail) > 200:
            return f"{self.err_msg} {self.err_msg_detail[:50]}...{self.err_msg_detail[-50:]}"
        return f"{self.err_msg} {self.err_msg_detail}"


# 当使用页面模拟点击时，找不到点击的按钮将抛出此异常
class ButtonNotExistError(BaseError):
    def __init__(self, err_msg):
        self.err_msg = err_msg
        self.err_msg_detail = "123"
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 网络错误
class NetworkError(BaseError):
    def __init__(self, err_msg_detail):
        self.err_msg = "网络错误，请检查代理或网络情况"
        self.err_msg_detail = err_msg_detail
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


class MyTimeoutError(BaseError):
    def __init__(self, err_msg_detail):
        self.err_msg = "请求超时"
        self.err_msg_detail = err_msg_detail
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 判断链接类型时，识别不到链接类型将抛出此异常
class LinktypeNotSupportError(BaseError):
    def __init__(self, err_msg_detail):
        self.err_msg = "链接类型错误或不支持"
        self.err_msg_detail = err_msg_detail
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 请求时服务器错误
class LinkServerRaiseError(BaseError):
    def __init__(self, err_msg_detail):
        self.err_msg = "请求的链接所在服务器抛出错误"
        self.err_msg_detail = err_msg_detail
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 找不到可下载元素
class CannotFoundElementError(BaseError):
    def __init__(self, err_msg_detail):
        self.err_msg = "找不到可下载元素"
        self.err_msg_detail = err_msg_detail
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 文件类型不支持下载时，将抛出此异常
# 如pixiv的动图
class FileCanNotDownloadError(BaseError):
    def __init__(self, err_msg_detail):
        self.err_msg = "文件类型不支持下载"
        self.err_msg_detail = err_msg_detail
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 插画作者信息不存在抛出此异常， 后续的步骤大多应该为向数据库作者表插入一条新的数据
class UserInfoNotExistError(BaseError):
    def __init__(self):
        self.err_msg = "用户信息不存在"
        self.err_msg_detail = ""
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 输入文件路径时，文件路径不存在将抛出此异常，后续一般是直接忽略该任务
class PathNotExistError(BaseError):
    def __init__(self, path):
        self.err_msg = "文件路径不存在"
        self.err_msg_detail = f"路径{path}不存在，请确认文件路径"
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 外部接口的API数额耗尽将抛出此异常
# 如Saucenao首先会尝试等待10秒，避免是由短配额抛出的异常，尝试次数超过之后，基本可以确定为长配额超出的异常，标记数据未完成，但不是失败
class OutOfRemainingError(BaseError):
    def __init__(self, detail):
        self.err_msg = "API配额耗尽"
        self.err_msg_detail = f"{detail}"
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 被retry装饰器修饰的函数，如果在尝试次数耗尽前仍抛出错误，则抛出这个错误，并附带最后一次抛出的错误的信息
class OutOfRetryError(BaseError):
    def __init__(self, detail):
        self.err_msg = "重试次数耗尽"
        self.err_msg_detail = f"{detail}"
        Exception.__init__(self, self.err_msg, self.err_msg_detail)


# 文件校验失败或者打开失败
class FileIOError(BaseError):
    def __init__(self, path):
        self.err_msg = "文件打开失败，请检查文件完整性"
        self.err_msg_detail = f"{path}"
        Exception.__init__(self, self.err_msg, self.err_msg_detail)
