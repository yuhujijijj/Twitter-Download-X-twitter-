import os
import pickle
import re
import time
import argparse
import json
import sys
import io
from datetime import datetime

if sys.platform == 'win32':
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)


class UserEntry:
    def __init__(self, screen_name, folder_path):
        self.screen_name = screen_name
        self.folder_path = folder_path
        self.name = None
        self.rest_id = None
        self.last_download_date = None
        self.file_count = 0
        self.cache_exists = False
    
    def to_dict(self):
        return {
            'screen_name': self.screen_name,
            'folder_path': self.folder_path,
            'name': self.name,
            'rest_id': self.rest_id,
            'last_download_date': self.last_download_date,
            'file_count': self.file_count,
            'cache_exists': self.cache_exists
        }
    
    @classmethod
    def from_dict(cls, data):
        entry = cls(data['screen_name'], data['folder_path'])
        entry.name = data.get('name')
        entry.rest_id = data.get('rest_id')
        entry.last_download_date = data.get('last_download_date')
        entry.file_count = data.get('file_count', 0)
        entry.cache_exists = data.get('cache_exists', False)
        return entry
    
    def __repr__(self):
        return f"UserEntry(screen_name={self.screen_name}, name={self.name}, last_download={self.last_download_date})"


def _load_settings():
    settings_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    settings_file = os.path.join(settings_dir, 'settings.json')
    if not os.path.exists(settings_file):
        settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
    with open(settings_file, 'r', encoding='utf8') as f:
        return json.load(f)


def scan_users(save_path=None):
    if save_path is None:
        try:
            settings = _load_settings()
            save_path = settings.get('save_path', '')
        except Exception:
            save_path = ''
    
    if not save_path or not os.path.exists(save_path):
        return []
    
    users = []
    for item in os.listdir(save_path):
        item_path = os.path.join(save_path, item)
        if os.path.isdir(item_path):
            if not item.startswith('.') and not item.startswith('_'):
                user_entry = UserEntry(item, item_path)
                analyze_user_folder(user_entry)
                users.append(user_entry)
    
    users.sort(key=lambda x: (x.last_download_date or '', x.screen_name), reverse=True)
    return users


def analyze_user_folder(user_entry):
    cache_path = os.path.join(user_entry.folder_path, 'user_cache.log')
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                user_cache = pickle.load(f)
            if user_entry.screen_name in user_cache:
                cache_time, user_data = user_cache[user_entry.screen_name]
                user_entry.name = user_data.get('name', user_entry.screen_name)
                user_entry.rest_id = user_data.get('rest_id')
            user_entry.cache_exists = True
        except Exception:
            pass
    
    if user_entry.name is None:
        user_entry.name = user_entry.screen_name
    
    files = []
    for f in os.listdir(user_entry.folder_path):
        f_path = os.path.join(user_entry.folder_path, f)
        if os.path.isfile(f_path):
            if not f.startswith('.') and not f.startswith('_'):
                files.append(f)
    
    user_entry.file_count = len(files)
    
    re_rule = r'\d{4}-\d{2}-\d{2}'
    last_date = None
    for f in sorted(files, reverse=True):
        match = re.findall(re_rule, f)
        if match:
            last_date = match[0]
            break
    
    if last_date:
        user_entry.last_download_date = last_date
    else:
        latest_mtime = 0
        for f in files:
            f_path = os.path.join(user_entry.folder_path, f)
            mtime = os.path.getmtime(f_path)
            if mtime > latest_mtime:
                latest_mtime = mtime
        if latest_mtime > 0:
            user_entry.last_download_date = datetime.fromtimestamp(latest_mtime).strftime('%Y-%m-%d')


def print_user_list(users):
    if not users:
        print("未找到任何已下载的用户")
        return
    
    print("\n" + "=" * 80)
    print(f"已发现 {len(users)} 个用户:")
    print("=" * 80)
    
    for i, user in enumerate(users, 1):
        last_download = user.last_download_date if user.last_download_date else "未知"
        print(f"{i:3d}. @{user.screen_name}")
        print(f"       昵称: {user.name}")
        print(f"       文件夹: {user.folder_path}")
        print(f"       文件数: {user.file_count}")
        print(f"       最后下载: {last_download}")
        print()


def get_user_choice(users):
    while True:
        print("请选择要更新的用户:")
        print("  输入序号选择单个用户")
        print("  输入 'all' 更新所有用户")
        print("  输入 'none' 或 'q' 退出")
        print("  输入多个序号用逗号分隔（如: 1,3,5）")
        
        choice = input("\n请输入选择: ").strip()
        
        if choice.lower() in ['none', 'q', 'quit', 'exit']:
            return []
        
        if choice.lower() == 'all':
            return users
        
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip()]
            selected = []
            for idx in indices:
                if 0 <= idx < len(users):
                    selected.append(users[idx])
                else:
                    print(f"警告: 序号 {idx + 1} 超出范围")
            return selected
        except ValueError:
            print("无效输入，请输入数字或 'all'")


def update_user(user_entry, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    
    log(f"\n{'=' * 60}")
    log(f"正在更新: @{user_entry.screen_name}")
    log(f"昵称: {user_entry.name}")
    log(f"{'=' * 60}")
    
    from user_info import User_info
    from main import main as download_main
    
    try:
        settings = _load_settings()
        settings['user_lst'] = user_entry.screen_name
        settings['autoSync'] = True
        
        user_info = User_info(user_entry.screen_name)
        user_info.save_path = user_entry.folder_path
        
        result = download_main(user_info)
        if result is False:
            log(f"\n@{user_entry.screen_name} 更新失败")
        else:
            log(f"\n@{user_entry.screen_name} 更新完成")
    except Exception as e:
        log(f"\n@{user_entry.screen_name} 更新异常: {e}")


def update_users(screen_names, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    
    try:
        settings = _load_settings()
        users = scan_users(settings.get('save_path'))
        
        selected_users = [u for u in users if u.screen_name in screen_names]
        
        log(f"\n即将更新 {len(selected_users)} 个用户:")
        for user in selected_users:
            log(f"  - @{user.screen_name}")
        
        _start = time.time()
        for user in selected_users:
            update_user(user, log_callback)
        
        log(f"\n{'=' * 60}")
        log("所有更新任务完成")
        log(f"总耗时: {time.time() - _start:.2f} 秒")
        log(f"{'=' * 60}")
    except Exception as e:
        log(f"更新失败: {e}")


def main_cli():
    try:
        settings = _load_settings()
        print(f"存储路径: {settings.get('save_path', '')}")
        
        users = scan_users(settings.get('save_path'))
        print_user_list(users)
        
        if not users:
            print("没有可更新的用户")
            return
        
        selected_users = get_user_choice(users)
        
        if not selected_users:
            print("未选择任何用户，退出")
            return
        
        print(f"\n即将更新 {len(selected_users)} 个用户:")
        for user in selected_users:
            print(f"  - @{user.screen_name}")
        
        confirm = input("\n确认继续? (y/n): ").strip().lower()
        if confirm != 'y':
            print("取消操作")
            return
        
        _start = time.time()
        for user in selected_users:
            update_user(user)
        
        print(f"\n{'=' * 60}")
        print("所有更新任务完成")
        print(f"总耗时: {time.time() - _start:.2f} 秒")
        print(f"{'=' * 60}")
    except Exception as e:
        print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(description='Twitter用户同步管理')
    parser.add_argument('--users', type=str, help='要更新的用户名列表，用逗号分隔')
    args = parser.parse_args()
    
    if args.users:
        screen_names = [u.strip() for u in args.users.split(',') if u.strip()]
        update_users(screen_names)
    else:
        main_cli()


if __name__ == '__main__':
    main()