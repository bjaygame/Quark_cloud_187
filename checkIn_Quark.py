import os 
import re 
import sys 
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

cookie_list = os.getenv("COOKIE_QUARK").split('\n|&&')

# 邮箱通知
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT", default=587)  # 587 TLS 端口，使用 465 代表 SSL
EMAIL = os.getenv("EMAIL")  # 你的邮箱
PASSWORD = os.getenv("PASSWORD")  # 你的 SMTP 授权码（不是邮箱密码）

email_config_is_ok = False

if SMTP_SERVER is not None and SMTP_PORT is not None and EMAIL is not None and PASSWORD is not None:
    email_config_is_ok = True

def send_email(body: str):
    SUBJECT = "夸克网盘自动签到"
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        msg["Subject"] = SUBJECT
        # 添加邮件正文
        msg.attach(MIMEText(body, "plain"))

        # 连接 SMTP 服务器
        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))
        if int(SMTP_PORT) == 587:
            server.starttls()  # 启用 TLS 加密
        server.login(EMAIL, PASSWORD)  # 登录 SMTP 服务器
        server.sendmail(EMAIL, EMAIL, msg.as_string())  # 发送邮件
        server.quit()  # 关闭连接
    except Exception as e:
        print(f"邮件发送失败: {e}")

# 添加 Server酱 推送函数
def send_to_server(title, desp):
    server_key = os.environ.get("SERVER_KEY")
    if not server_key:
        print("未配置SERVER_KEY推送密钥")
        return
    url = f"https://sctapi.ftqq.com/{server_key}.send"
    data = {
        "title": title,
        "desp": desp
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Server酱推送成功")
        else:
            print(f"Server酱推送失败：{response.text}")
    except Exception as e:
        print(f"Server酱推送异常：{str(e)}")

# 替代 notify 功能
def send(title, message):
    print(f"{title}: {message}")
    send_to_server(title, message)
    if email_config_is_ok:
            send_email(message)

# 获取环境变量 
def get_env(): 
    # 判断 COOKIE_QUARK是否存在于环境变量 
    if "COOKIE_QUARK" in os.environ: 
        # 读取系统变量以 \n 或 && 分割变量 
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK')) 
    else: 
        # 标准日志输出 
        print('❌未添加COOKIE_QUARK变量') 
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量') 
        # 脚本退出 
        sys.exit(0) 

    return cookie_list 

# 其他代码...

class Quark:
    '''
    Quark类封装了签到、领取签到奖励的方法
    '''
    def __init__(self, user_data):
        '''
        初始化方法
        :param user_data: 用户信息，用于后续的请求
        '''
        self.param = user_data

    def convert_bytes(self, b):
        '''
        将字节转换为 MB GB TB
        :param b: 字节数
        :return: 返回 MB GB TB
        '''
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "iphone",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        response = requests.get(url=url, params=querystring).json()
        #print(response)
        if response.get("data"):
            return response["data"]
        else:
            return False

    def get_growth_sign(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "iphone",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        response = requests.post(url=url, json=data, params=querystring).json()
        #print(response)
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response["message"]

    def queryBalance(self):
        '''
        查询抽奖余额
        '''
        url = "https://coral2.quark.cn/currency/v1/queryBalance"
        querystring = {
            "moduleCode": "1f3563d38896438db994f118d4ff53cb",
            "kps": self.param.get('kps'),
        }
        response = requests.get(url=url, params=querystring).json()
        # print(response)
        if response.get("data"):
            return response["data"]["balance"]
        else:
            return response["msg"]

    def do_sign(self):
        '''
        执行签到任务
        :return: 返回一个字符串，包含签到结果
        '''
        log = ""
        # 每日领空间
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
                f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量：")
            if "sign_reward" in growth_info['cap_composition']:
                log += f"{self.convert_bytes(growth_info['cap_composition']['sign_reward'])}\n"
            else:
                log += "0 MB\n"
            if growth_info["cap_sign"]["sign_daily"]:
                log += (
                    f"✅ 签到日志: 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                    f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
                )
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += (
                        f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                        f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                    )
                else:
                    log += f"❌ 签到异常: {sign_return}\n"
        else:
            # log += f"❌ 签到异常: 获取成长信息失败\n"
            raise Exception("❌ 签到异常: 获取成长信息失败")  # 适用于单账号情形，当 cookie 值失效后直接报错，方便通过 github action 的操作系统来进行提醒 如果你使用的是多账号签到的话，不要跟进此更新

        return log


def main():
    '''
    主函数
    :return: 返回一个字符串，包含签到结果
    '''
    msg = ""
    global cookie_quark
    cookie_quark = get_env()

    print("✅ 检测到共", len(cookie_quark), "个夸克账号\n")

    i = 0
    while i < len(cookie_quark):
        # 获取user_data参数
        user_data = {}  # 用户信息
        for a in cookie_quark[i].replace(" ", "").split(';'):
            if not a == '':
                user_data.update({a[0:a.index('=')]: a[a.index('=') + 1:]})
        # print(user_data)
        # 开始任务
        log = f"🙍🏻‍♂️ 第{i + 1}个账号"
        msg += log
        # 登录
        log = Quark(user_data).do_sign()
        msg += log + "\n"

        i += 1

    # print(msg)

    try:
        send('夸克自动签到', msg)
    except Exception as err:
        print('%s\n❌ 错误，请查看运行日志！' % err)

    return msg[:-1]


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
