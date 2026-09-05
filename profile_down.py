import os
import httpx
import re
import json
from url_utils import quote_url
from common import get_headers, get_proxies, load_settings

# 读取配置文件
settings = load_settings()

# 配置变量
_path = 'profile'
user_lst = [user.strip() for user in settings['user_lst'].replace('\n', ',').split(',') if user.strip()]

_headers = get_headers().copy()

# 代理配置
proxies = get_proxies()

def profile_down(screen_name, path):

    url = 'https://twitter.com/i/api/graphql/gEyDv8Fmv2BVTYIAf32nbA/UserByScreenName?variables={"screen_name":"' + screen_name + '","withGrokTranslatedBio":false}&features={"hidden_profile_subscriptions_enabled":true,"payments_enabled":false,"rweb_xchat_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}&fieldToggles={"withAuxiliaryUserLabels":true}'
    response = httpx.get(quote_url(url), headers=_headers, proxy=proxies).text 
    raw_data = json.loads(response)
    try:
        avatar_url = raw_data['data']['user']['result']['avatar']['image_url']
        description = raw_data['data']['user']['result']['legacy']['description']
        if 'profile_banner_url' not in raw_data['data']['user']['result']['legacy']:
            profile_banner_url = None
        else:
            profile_banner_url = raw_data['data']['user']['result']['legacy']['profile_banner_url']

        avatar_url = re.sub(r'_normal(\.\w+)$', r'_400x400\1', avatar_url) 

        avatar_response = httpx.get(avatar_url, headers=_headers, proxy=proxies)
        profile_banner_response = httpx.get(profile_banner_url, headers=_headers, proxy=proxies) if profile_banner_url else None

        with open(path + os.sep + screen_name + '_avatar.jpg', 'wb') as f:
            f.write(avatar_response.content)
        if profile_banner_response:
            with open(path + os.sep + screen_name + '_banner.jpg', 'wb') as f:
                f.write(profile_banner_response.content)
        with open(path + os.sep + screen_name + '_description.txt', 'w', encoding='utf-8') as f:
            f.write(description)
        return False  # 成功时返回False
    
    except Exception as e:
        print(f'用户: {screen_name}  失败: {e}')
        return True  # 失败时返回True



if __name__ == '__main__':
    if not os.path.exists(_path):
        os.makedirs(_path)
    for user in user_lst:
        _headers['referer'] = 'https://twitter.com/' + user

        print(f'\n正在获取用户: {user}')
        if not profile_down(user, _path):
            print('---------Completed---------')

    print('\nAll tasks completed.')
