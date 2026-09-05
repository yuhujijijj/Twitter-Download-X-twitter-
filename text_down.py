import os
import re
import json
import csv
import time
from datetime import datetime
from user_info import User_info
from url_utils import quote_url
from common import get_settings, load_settings, get_headers, make_request, time2stamp, stamp2time


class csv_gen():
    def __init__(self, save_path:str, user_name, screen_name, tweet_range) -> None:
        import os
        csv_filename = f'{screen_name}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}-text.csv'
        csv_path = os.path.join(save_path, csv_filename)
        self.f = open(csv_path, 'w', encoding='utf-8-sig', newline='')
        self.writer = csv.writer(self.f)

        self.writer.writerow([user_name, '@' + screen_name])
        self.writer.writerow(['Tweet Range : ' + tweet_range])
        self.writer.writerow(['Save Path : ' + save_path])
        main_par = ['Display Name', 'User Name', 'Tweet Date', 'Tweet URL', 'Tweet Content', 'Favorite Count', 
                    'Retweet Count', 'Reply Count']
        self.writer.writerow(main_par)

    def csv_close(self):
        self.f.close()

    def data_input(self, main_par_info:list) -> None:
        main_par_info[2] = stamp2time(main_par_info[2])
        self.writer.writerow(main_par_info)


def time_comparison(now, start_time_stamp, end_time_stamp):
    start_label = True
    start_down = False
    if now >= start_time_stamp and now <= end_time_stamp:
        start_down = True
    elif now < start_time_stamp:
        start_label = False
    return [start_down, start_label]


class text_down():
    def __init__(self, screen_name):
        settings = get_settings()
        
        self._user_info = User_info(screen_name)
        self._headers = get_headers().copy()
        self._headers['referer'] = 'https://twitter.com/' + screen_name
        
        self.folder_path = os.path.join(settings['save_path'], screen_name) + os.sep
        
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        self.time_range = settings.get('time_range', '')
        if self.time_range:
            start_time, end_time = self.time_range.split(':')
            self.start_time_stamp = time2stamp(start_time)
            self.end_time_stamp = time2stamp(end_time)
        else:
            self.start_time_stamp = 655028357000
            self.end_time_stamp = 2548484357000
        
        self.has_retweet = settings.get('has_retweet', False)

        self.csv_file = csv_gen(self.folder_path, self._user_info.name, self._user_info.screen_name, self.time_range)

        self.cursor = ''

        self.get_clean_save()

        self.csv_file.csv_close()

    def get_clean_save(self):
        while True:
            url = 'https://twitter.com/i/api/graphql/9zyyd1hebl7oNWIPdA8HRw/UserTweets?variables={"userId":"' + self._user_info.rest_id + '","count":20,"cursor":"' + self.cursor + '","includePromotedContent":true,"withQuickPromoteEligibilityTweetFields":true,"withVoice":true,"withV2Timeline":true}&features={"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"tweet_with_visibility_results_prefer_gql_media_interstitial_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}&fieldToggles={"withArticlePlainText":false}'

            response = make_request(url)
            if not response:
                return
                
            try:
                raw_data = json.loads(response)
            except Exception:
                if 'Rate limit exceeded' in response:
                    print('API次数已超限')
                else:
                    print('获取数据失败')
                print(response)
                return
                
            try:
                raw_tweet_lst = raw_data['data']['user']['result']['timeline_v2']['timeline']['instructions'][-1]['entries']
            except Exception:
                return
                
            if len(raw_tweet_lst) == 2:
                return
            if self.cursor == raw_tweet_lst[-1]['content']['value']:
                return
            self.cursor = raw_tweet_lst[-1]['content']['value']

            for tweet in raw_tweet_lst:
                if 'promoted-tweet' in tweet['entryId']:
                    continue
                if 'tweet' in tweet['entryId']:
                    raw_text = tweet['content']['itemContent']['tweet_results']['result']
                    if 'tweet' in raw_text:
                        raw_text = raw_text['tweet']
                    try:
                        _time_stamp = int(raw_text['edit_control']['editable_until_msecs']) - 3600000
                    except Exception:
                        if 'edit_control_initial' in raw_text['edit_control']:
                            _time_stamp = int(raw_text['edit_control']['edit_control_initial']['editable_until_msecs']) - 3600000
                        else:
                            continue
                    if 'retweeted_status_result' in raw_text['legacy']:
                        if self.has_retweet:
                            raw_text = raw_text['legacy']['retweeted_status_result']['result']
                            if 'tweet' in raw_text:
                                raw_text = raw_text['tweet']
                            _display_name = raw_text['core']['user_results']['result']['legacy']['name']
                            _screen_name = '@' + raw_text['core']['user_results']['result']['legacy']['screen_name']
                        else:
                            continue
                    else:
                        _display_name = ''
                        _screen_name = ''

                    _results = time_comparison(_time_stamp, self.start_time_stamp, self.end_time_stamp)
                    if not _results[1]:
                        return
                    if not _results[0]:
                        continue
                    
                    _Favorite_Count = raw_text['legacy']['favorite_count']
                    _Retweet_Count = raw_text['legacy']['retweet_count']
                    _Reply_Count = raw_text['legacy']['reply_count']
                    _status_id = raw_text['legacy']['conversation_id_str']
                    screen_name = raw_text['core']['user_results']['result']['legacy']['screen_name']
                    _tweet_url = f'https://twitter.com/{screen_name}/status/{_status_id}'
                    if 'note_tweet' in raw_text:
                        _tweet_content = raw_text['note_tweet']['note_tweet_results']['result']['text'].split('https://t.co/')[0]
                    else:
                        _tweet_content = raw_text['legacy']['full_text'].split('https://t.co/')[0]

                    self.csv_file.data_input([_display_name, _screen_name, _time_stamp, _tweet_url, _tweet_content, _Favorite_Count, _Retweet_Count, _Reply_Count])


def main():
    load_settings()
    settings = get_settings()
    
    _headers = get_headers()
    
    user_lst = [user.strip() for user in settings['user_lst'].replace('\n', ',').split(',') if user.strip()]
    
    def get_other_info(_user_info):
        url = 'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName?variables={"screen_name":"' + _user_info.screen_name + '","withSafetyModeUserFields":false}&features={"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}&fieldToggles={"withAuxiliaryUserLabels":false}'
        response = make_request(url)
        if not response:
            print('获取信息失败')
            return False
        try:
            raw_data = json.loads(response)
            _user_info.rest_id = raw_data['data']['user']['result']['rest_id']
            _user_info.name = raw_data['data']['user']['result']['legacy']['name']
            _user_info.statuses_count = raw_data['data']['user']['result']['legacy']['statuses_count']
            _user_info.media_count = raw_data['data']['user']['result']['legacy']['media_count']
        except Exception:
            print('获取信息失败')
            return False
        return True
    
    def print_info(_user_info):
        print(
            f'''
            <======基本信息=====>
            昵称:{_user_info.name}
            用户名:{_user_info.screen_name}
            数字ID:{_user_info.rest_id}
            总推数(含转推):{_user_info.statuses_count}
            含图片/视频/音频推数(不含转推):{_user_info.media_count}
            <==================>
            开始爬取...
            '''
        )
    
    for user in user_lst:
        _user_info = User_info(user)
        if not get_other_info(_user_info):
            continue
        print_info(_user_info)
        text_down(user)
    print('完成 (๑´ڡ`๑)')


if __name__ == '__main__':
    main()