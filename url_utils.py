


import urllib.parse

def quote_url(url):
    # 首先替换大括号，因为它们在Twitter API URL中是特殊的
    url = url.replace('{','%7B').replace('}','%7D')
    # 然后对URL进行标准编码，确保其他特殊字符被正确处理
    return urllib.parse.quote(url, safe=':/?=&%')