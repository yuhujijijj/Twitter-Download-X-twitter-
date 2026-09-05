import re
import time
from datetime import datetime
import os
import json
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)

def del_special_char(string):
    string = re.sub(r'[^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3040-\u31FF\.]', '', string)
    return string

def stamp2time(msecs_stamp: int) -> str:
    timeArray = time.localtime(msecs_stamp / 1000)
    otherStyleTime = time.strftime("%Y-%m-%d %H-%M", timeArray)
    return otherStyleTime

def time2stamp(timestr: str) -> int:
    datetime_obj = datetime.strptime(timestr, "%Y-%m-%d")
    msecs_stamp = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
    return msecs_stamp

def time_comparison(now, start, end):
    start_label = True
    start_down = False
    if now >= start and now <= end:
        start_down = True
    elif now < start:
        start_label = False
    return [start_down, start_label]

_settings = None
_headers = None
_proxies = None
_request_count = 0
_down_count = 0
_last_request_time = 0


def _settings_path():
    if getattr(sys, 'frozen', False):
        external_path = Path(sys.executable).with_name('settings.json')
        if external_path.exists():
            return external_path
    return Path(__file__).with_name('settings.json')

def load_settings():
    global _settings, _headers, _proxies
    
    settings_file = _settings_path()
    with settings_file.open('r', encoding='utf8') as f:
        _settings = json.load(f)

    _settings.setdefault('save_path', '')
    _settings.setdefault('cookie', '')
    cookie = os.environ.get('TWITTER_COOKIE', '').strip() or _settings['cookie'].strip()
    if not cookie:
        raise RuntimeError(
            '未配置 Cookie。请在 GUI 中填写，或设置环境变量 TWITTER_COOKIE；不要将 Cookie 提交到 Git。'
        )
    
    if not _settings['save_path'].strip():
        raise RuntimeError('未配置下载地址，请先在 GUI 中选择一个下载文件夹并保存配置。')
    _settings['save_path'] = os.path.abspath(os.path.expanduser(_settings['save_path'])) + os.sep
    
    _headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    }
    _headers['cookie'] = cookie
    
    csrf_match = re.search(r'(?:^|;)\s*ct0=([^;]+)', cookie)
    if not csrf_match:
        raise ValueError('Cookie 中缺少 ct0 字段，请提供包含 auth_token 和 ct0 的有效 Cookie。')
    _headers['x-csrf-token'] = csrf_match.group(1)
    
    proxy_value = _settings.get('proxy', '')
    _proxies = proxy_value if proxy_value and proxy_value.strip() else None
    
    return _settings

def get_settings():
    if _settings is None:
        load_settings()
    return _settings

def get_headers():
    if _headers is None:
        load_settings()
    return _headers

def get_proxies():
    if _proxies is None:
        load_settings()
    return _proxies

def make_request(url, max_retries=3, method='GET', json_data=None):
    global _request_count, _last_request_time, _settings, _proxies, _headers
    
    import httpx
    from urllib.parse import urlparse, parse_qs
    
    if _settings is None:
        load_settings()
    
    current_time = time.time()
    request_interval = _settings.get('request_interval', 0.5)
    if current_time - _last_request_time < request_interval:
        time.sleep(request_interval - (current_time - _last_request_time))
    
    _last_request_time = time.time()
    
    for attempt in range(max_retries):
        try:
            if method.upper() == 'POST':
                if json_data is None:
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)
                    post_data = {}
                    for key, value in query_params.items():
                        if len(value) == 1:
                            try:
                                post_data[key] = json.loads(value[0])
                            except:
                                post_data[key] = value[0]
                    url = parsed.scheme + '://' + parsed.netloc + parsed.path
                    json_data = post_data
                response = httpx.post(url, headers=_headers, proxy=_proxies, json=json_data)
            else:
                response = httpx.get(url, headers=_headers, proxy=_proxies)
            _request_count += 1
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"API限流，等待 {retry_after} 秒后重试...")
                time.sleep(retry_after)
                continue
                
            if response.status_code == 200:
                return response.text
            else:
                print(f"请求失败，状态码: {response.status_code}")
                try:
                    error_content = response.text[:500] if response.text else "无响应内容"
                    print(f"错误响应: {error_content}")
                except:
                    pass
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
                
        except Exception as e:
            print(f"请求异常: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    
    return None

def get_other_info(_user_info, cache_data=None):
    if _settings is None:
        load_settings()
    
    if cache_data and _settings.get('down_log'):
        cached_info = cache_data.get_user_info(_user_info.screen_name)
        if cached_info:
            _user_info.rest_id = cached_info['rest_id']
            _user_info.name = cached_info['name']
            _user_info.statuses_count = cached_info['statuses_count']
            _user_info.media_count = cached_info['media_count']
            print(f"从缓存中获取用户信息: {_user_info.screen_name}")
            return True
    
    url = 'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName'
    json_data = {
        'variables': {
            'screen_name': _user_info.screen_name,
            'withSafetyModeUserFields': False
        },
        'features': {
            'hidden_profile_likes_enabled': False,
            'hidden_profile_subscriptions_enabled': False,
            'responsive_web_graphql_exclude_directive_enabled': True,
            'verified_phone_label_enabled': False,
            'subscriptions_verification_info_verified_since_enabled': True,
            'highlights_tweets_tab_ui_enabled': True,
            'creator_subscriptions_tweet_preview_api_enabled': True,
            'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
            'responsive_web_graphql_timeline_navigation_enabled': True
        },
        'fieldToggles': {
            'withAuxiliaryUserLabels': False
        }
    }
    
    response = make_request(url, method='POST', json_data=json_data)
    if not response:
        print('获取信息失败: 请求失败')
        return False
        
    try:
        raw_data = json.loads(response)
        _user_info.rest_id = raw_data['data']['user']['result']['rest_id']
        _user_info.name = raw_data['data']['user']['result']['legacy']['name']
        _user_info.statuses_count = raw_data['data']['user']['result']['legacy']['statuses_count']
        _user_info.media_count = raw_data['data']['user']['result']['legacy']['media_count']
        
        if cache_data and _settings.get('down_log'):
            user_data = {
                'rest_id': _user_info.rest_id,
                'name': _user_info.name,
                'statuses_count': _user_info.statuses_count,
                'media_count': _user_info.media_count
            }
            cache_data.set_user_info(_user_info.screen_name, user_data)
            print(f"已缓存用户信息: {_user_info.screen_name}")
            
    except Exception as e:
        print('获取信息失败')
        print(e)
        print(response)
        return False
    return True

def print_info(_user_info):
    estimated_total = _user_info.media_count * 3 if _user_info.media_count else 0
    print(
        f'''
        <======基本信息=====>
        昵称:{_user_info.name.encode('utf-8', errors='replace').decode('utf-8')}
        用户名:{_user_info.screen_name}
        数字ID:{_user_info.rest_id}
        总推数(含转推):{_user_info.statuses_count}
        含图片/视频/音频推数(不含转推):{_user_info.media_count}
        预估媒体文件数:约{estimated_total}个
        <==================>
        开始爬取...
        ''',
        flush=True
    )

def get_stats():
    return {
        'request_count': _request_count,
        'down_count': _down_count
    }

def reset_stats():
    global _request_count, _down_count, _last_request_time
    _request_count = 0
    _down_count = 0
    _last_request_time = 0