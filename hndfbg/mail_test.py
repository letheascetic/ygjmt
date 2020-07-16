# coding: utf-8


import time
import smtplib
from email.utils import formataddr
from email.header import Header
from email.mime.text import MIMEText


def send_mail(goods_id, info, users):
    goods_title = info['title']
    content = str(info)

    from_addr = 'yizhifight@163.com'    # 邮件发送账号
    # to_addrs = 'wc1148728402@163.com'   # 接收邮件账号

    code = 'MQQAHYSFJKZDZWIE'       # 授权码（这个要填自己获取到的）
    smtp_server = 'smtp.163.com'  # 固定写死
    smtp_port = 465  # 固定端口

    users_list = list(users)
    user_count = len(users_list)
    n = 0
    while n < user_count:
        to_addrs = users_list[n:n + 30]
        n = n + 30
        i = 0
        while i < 3:
            try:
                # 配置服务器
                stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
                stmp.login(from_addr, code)
                # 组装发送内容
                message = MIMEText(content, 'plain')  # 发送的内容
                message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
                message['To'] = ','.join(to_addrs)  # 收件人
                message['Cc'] = from_addr
                subject = '{0}-{1}'.format('海免补货', goods_title)
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                break
            except Exception as e:
                i = i + 1
                print('send mail[{0}][{1}] failed; [{2}].'.format(info, users, e))
                time.sleep(2)


def mail_test():
    while True:
        goods_id = '2c9194587219d0ae017219dc9774090b'
        info = {'title': '倩碧（Clinique）匀净卓研淡斑双效精华露两支装50ML×2瓶',
                'url': 'https://m.yuegowu.com/goods-detail/2c9194587219d0ae017219dc9774090b?_t=24751&from=groupmessage&isappinstalled=0',
                'status': '在售', '库存': 2}
        users = ['1148728402@qq.com']
        send_mail(goods_id, info, users)
        time.sleep(2)


if __name__ == '__main__':
    mail_test()
    pass
