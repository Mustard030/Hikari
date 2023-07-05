import aiohttp

from hikari.common.const import PIXIV_PROXY_WITH_P, PIXIV_PROXY_WITHOUT_P, PIXIV_INFO_URL, TWEET_CONTENT, SANKAKU_INFO
from hikari.common.decorator import retry
from hikari.common.exceptions import NetworkError
from hikari.config.hikari_config import config
from hikari.common.const import DEFAULT_USER_AGENT, ACCEPT_LANGUAGE


# Network
def proxy_path():
    return f"{config['proxy']['ip']}:{config['proxy']['port']}"


# Pixiv
def pixiv_proxy_url(pixiv_id: int, p: int = 0):
    if p != 0:
        return PIXIV_PROXY_WITH_P.format(pixiv_id=pixiv_id, p=p)

    return PIXIV_PROXY_WITHOUT_P.format(pixiv_id=pixiv_id)


def pixiv_info_url(pixiv_id):
    return PIXIV_INFO_URL.format(pixiv_id=pixiv_id)


@retry(times=3, wait=10)
async def like_pixiv_image(pixiv_id) -> (bool, str):
    url = "https://www.pixiv.net/ajax/illusts/bookmarks/add"
    header = {
        "user-agent": DEFAULT_USER_AGENT,
        "accept-language": ACCEPT_LANGUAGE,
        "x-csrf-token": config["account"]["pixiv"]["cookies"]["x_csrf_token"],
    }
    cookies = {
        "PHPSESSID": config["account"]["pixiv"]["cookies"]["PHPSESSID"],
    }
    payload = {"illust_id": str(pixiv_id), "restrict": 0, "comment": "", "tags": []}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=header, cookies=cookies, proxy=proxy_path()
                                ) as resp:
            t = await resp.json()
            return t['error'], t['message']


def sankaku_info_url():
    return SANKAKU_INFO


def sankaku_post_url(post_id):
    return f"https://beta.sankakucomplex.com/zh-CN/post/show/{post_id}"


# Twitter  封存！！！
def _twitter_info_url(tweet_id):
    return TWEET_CONTENT.format(
        query_id=config['account']['twitter']['query']['query_id_TweetInfo'],
        tweet_id=tweet_id
    )


def _twitter_header():
    header = {
        "authorization": config["account"]["twitter"]["cookies"]["authorization"],
        "x-csrf-token": config["account"]["twitter"]["cookies"]["x_csrf_token"],
    }
    return header


def _twitter_cookies():
    cookies = {
        "auth_token": config["account"]["twitter"]["cookies"]["auth_token"],
        "ct0": config["account"]["twitter"]["cookies"]["x_csrf_token"],
    }
    return cookies


async def _tweet_brief(tweet_id) -> dict:
    """
    获取推文信息
    :return: 推文信息json
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_twitter_info_url(tweet_id),
                                   headers=_twitter_header(),
                                   cookies=_twitter_cookies(),
                                   proxy=proxy_path()
                                   ) as resp:
                return await resp.json()
    except OSError as e:
        raise NetworkError(e)


async def _like_tweet(tweet_id, like=True) -> (bool, str):
    """
    点赞或取消点赞推文
    :param tweet_id: 推文id
    :param like: True为赞，False为取消赞
    :return: success, error_message
    """
    query_id_favorite = config['account']['twitter']['query']['query_id_Favorite']
    query_id_unfavorite = config['account']['twitter']['query']['query_id_Unfavorite']
    query_id = query_id_favorite if like else query_id_unfavorite

    mark_favorite = "FavoriteTweet"
    mark_unfavorite = "UnfavoriteTweet"
    mark = mark_favorite if like else mark_unfavorite

    payload = {
        "variables": {
            "tweet_id": tweet_id
        },
        "queryId": query_id
    }

    url = f"https://twitter.com/i/api/graphql/{query_id}/{mark}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=_twitter_header(), cookies=_twitter_cookies(),
                                proxy=proxy_path()
                                ) as resp:
            t = await resp.json()
            if t['data']:
                success = True
                error_msg = ''
            else:
                success = False
                error_msg = t['errors'][0]['message']
            return success, error_msg


async def follow_twitter_user(rest_id: str):
    """
    rest_id 通常在推文信息的json中
    resp_json['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries']
    tweet_detail['content']['itemContent']['tweet_results']['result']['core']['user_results']['result']['rest_id']
    :param rest_id: 用户的一个数字id
    :return:
    """
    url = "https://api.twitter.com/1.1/friendships/create.json"
    payload = {
        "include_profile_interstitial_type": 1,
        "include_blocking": 1,
        "include_blocked_by": 1,
        "include_followed_by": 1,
        "include_want_retweets": 1,
        "include_mute_edge": 1,
        "include_can_dm": 1,
        "include_can_media_tag": 1,
        "include_ext_has_nft_avatar": 1,
        "include_ext_is_blue_verified": 1,
        "include_ext_verified_type": 1,
        "skip_status": 1,
        "user_id": str(rest_id)
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url,
                                    json=payload,
                                    headers=_twitter_header(),
                                    cookies=_twitter_cookies(),
                                    proxy=proxy_path()
                                    ) as resp:
                return await resp.json()
    except OSError as e:
        raise NetworkError(e)


# utils
def index_generator(start=0):
    while True:
        yield start
        start += 1
