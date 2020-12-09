# coding: utf-8


import random
import logging
import smtplib
import datetime

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class Mailer(object):
    def __init__(self, config):
        self.name = 'mailer'
        self._config = config

    def send_subscriber_mail(self, user, mail_title, goods_info):
        # 用户有邮箱和授权码，且邮箱状态正常，则使用该邮箱发送
        if user.email and user.email_code and user.email_status < 10:
        # if user.email and user.email_code:
            from_addr, code = user.email, user.email_code.strip()
            to_addrs = [from_addr]
        elif user.email and user.email_code and user.email_status >= 10 and \
                (datetime.datetime.now() - user.update_time).total_seconds() > 6 * 3600:
            from_addr, code = user.email, user.email_code.strip()
            to_addrs = [from_addr]
        # 用户有邮箱和授权码，且邮箱状态不正常，则使用服务器的邮箱发送
        # elif user.email and user.email_code and user.email_status >= 10:
        #     server_mailer = random.choice(self._config['SERVER_MAILERS'])
        #     from_addr, code = server_mailer['email'], server_mailer['code']
        #     to_addrs = [user.email]
        # 用户有邮箱但没有授权码，则使用服务器的邮箱发送
        elif user.email and not user.email_code:
            server_mailer = random.choice(self._config['SERVER_MAILERS'])
            from_addr, code = server_mailer['email'], server_mailer['code']
            to_addrs = [user.email]
        # 用户邮箱和授权码都没有，则不发送
        else:
            logger.info('user[{0}] has no email, no need to send mail.')
            return {'code': 0, 'msg': 'no email', 'mailer': None}

        content = {'商品': goods_info['title'], '状态': goods_info['status'], '库存': goods_info['stock'],
                   '价格': goods_info['price'], '折扣': goods_info['discount'], '链接': goods_info['url']}
        content = str(content)

        # from_addr, code = 'letheascetic@163.com', 'BGDAEEMWDFDGBRVQ'
        # to_addrs = [from_addr]

        if '163.com' in from_addr:
            smtp_server = 'smtp.163.com'      # 固定写死
            smtp_port = 465                   # 固定端口
        else:
            smtp_server = 'smtp.qq.com'      # 固定写死
            smtp_port = 465                  # 固定端口

        try:
            # 配置服务器
            stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
            stmp.login(from_addr, code)

            # 组装发送内容
            message = MIMEText(content, 'plain')  # 发送的内容
            message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
            message['To'] = ','.join(to_addrs)  # 收件人

            subject = '{0}: 库存{1}-{2}'.format('cdf北京', goods_info['stock'], mail_title)
            message['Subject'] = Header(subject)  # 邮件标题
            stmp.sendmail(from_addr, to_addrs, message.as_string())

            return {'code': 0, 'msg': 'success', 'mailer': from_addr}
        except Exception as e:
            logger.exception('user[{0}] send mail[{1}] with mailer[{2}|{3}] exception[{4}].'.format(user, mail_title,
                                                                                                    from_addr, code, e))
            return {'code': 1, 'msg': 'exception', 'mailer': from_addr}

    def send_sys_subscriber_mail(self, mail_title, goods_info, users):
        sys_mailer = self._config['SYS_MAILER']
        from_addr, code = sys_mailer['email'], sys_mailer['code']
        to_addrs = [from_addr]

        # from_addr, code = 'letheascetic@163.com', 'BGDAEEMWDFDGBRVQ'
        # to_addrs = [from_addr]

        content = {'商品': goods_info['title'], '状态': goods_info['status'], '库存': goods_info['stock'],
                   '价格': goods_info['price'], '折扣': goods_info['discount'], '链接': goods_info['url']}
        content = str('[{0}]\n\nTo:\n[{1}]\n'.format(content, users))

        if '163.com' in from_addr:
            smtp_server = 'smtp.163.com'      # 固定写死
            smtp_port = 465                   # 固定端口
        else:
            smtp_server = 'smtp.qq.com'      # 固定写死
            smtp_port = 465                  # 固定端口

        try:
            # 配置服务器
            stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
            stmp.login(from_addr, code)

            # 组装发送内容
            message = MIMEText(content, 'plain')  # 发送的内容
            message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
            message['To'] = ','.join(to_addrs)  # 收件人

            subject = '{0}: 库存{1}-{2}'.format('cdf北京', goods_info['stock'], mail_title)
            message['Subject'] = Header(subject)  # 邮件标题
            stmp.sendmail(from_addr, to_addrs, message.as_string())

            return {'code': 0, 'msg': 'success', 'mailer': from_addr}
        except Exception as e:
            logger.exception('send sys mail[{0}][{1}] exception[{1}].'.format(sys_mailer, mail_title, e))
            return {'code': 1, 'msg': 'exception', 'mailer': from_addr}

    def send_report_mail(self, mail_title, ip_statistics, user_statistics, goods_statistics):
        sys_mailer = self._config['SYS_MAILER']
        from_addr, code = sys_mailer['email'], sys_mailer['code']
        to_addrs = [from_addr]

        ip_content = 'IP使用情况统计：\n\t{0}\n'.format(ip_statistics)
        user_content = '用户使用情况统计：\n\t{0}\n'.format(user_statistics)
        goods_content = '产品使用情况统计：\n\t{0}\n'.format(goods_statistics)

        content = ip_content + user_content + goods_content

        if '163.com' in from_addr:
            smtp_server = 'smtp.163.com'      # 固定写死
            smtp_port = 465                   # 固定端口
        else:
            smtp_server = 'smtp.qq.com'      # 固定写死
            smtp_port = 465                  # 固定端口

        try:
            # 配置服务器
            stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
            stmp.login(from_addr, code)

            # 组装发送内容
            message = MIMEText(content, 'plain')  # 发送的内容
            message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
            message['To'] = ','.join(to_addrs)  # 收件人

            subject = '{0}: {1}'.format('cdf北京', mail_title)
            message['Subject'] = Header(subject)  # 邮件标题
            stmp.sendmail(from_addr, to_addrs, message.as_string())

            return {'code': 0, 'msg': 'success', 'mailer': from_addr}
        except Exception as e:
            logger.exception('send report mail[{0}][{1}] exception[{1}].'.format(sys_mailer, mail_title, e))
            return {'code': 1, 'msg': 'exception', 'mailer': from_addr}
