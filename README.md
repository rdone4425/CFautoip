# CFautoip
自动更新优选CF的IP


每分钟无日志运行DDNS
* * * * * /usr/bin/python3 /root/CFautoip/ddns.py >/dev/null 2>&1
