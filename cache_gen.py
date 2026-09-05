import os
import pickle
import time

class cache_gen():

    def __init__(self, save_path) -> None:
        self.cache_path = save_path + os.sep + "cache_data.log"

        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'rb') as f:
                self.cache_data = pickle.load(f)
        else:
            self.cache_data = set()
            
        # 用户信息缓存路径
        self.user_cache_path = save_path + os.sep + "user_cache.log"
        if os.path.exists(self.user_cache_path):
            with open(self.user_cache_path, 'rb') as f:
                self.user_cache = pickle.load(f)
        else:
            self.user_cache = {}

    def save(self):
        try:
            with open(self.cache_path, 'wb') as f:
                pickle.dump(self.cache_data, f)
            with open(self.user_cache_path, 'wb') as f:
                pickle.dump(self.user_cache, f)
        except:
            pass

    def __del__(self):
        try:
            self.save()
        except:
            pass

    def add(self, element):
        self.cache_data.add(element)

    def is_present(self, element):
        if element in self.cache_data:
            return False
        else:
            self.add(element)
            return True
            
    # 用户信息缓存方法
    def get_user_info(self, screen_name):
        """获取缓存的用户信息，如果不存在或超过24小时则返回None"""
        if screen_name in self.user_cache:
            cache_time, user_data = self.user_cache[screen_name]
            # 如果缓存超过24小时，则重新获取
            if time.time() - cache_time < 86400:  # 24小时 = 86400秒
                return user_data
        return None
        
    def set_user_info(self, screen_name, user_data):
        """缓存用户信息"""
        self.user_cache[screen_name] = (time.time(), user_data)


