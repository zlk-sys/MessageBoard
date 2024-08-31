# MessageBoard

留言板 | MessageBoard

该程序接入了极验行为验，可防止通过API无限提交留言



后端程序：server.py

需要设置自己的极验API、KEY，以及后台管理密码。

server.py不建议放置在网站目录中



建议将/admin目录设置nginx加密访问

在/eula/index.html设置自己的使用协议

需要在 index.html 和 admin/index.html 将 https://api.example.com 替换为自己的后端API地址


