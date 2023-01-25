"""
长链接请求,后期处理
"""

import httpx
from httpx import RemoteProtocolError, ConnectTimeout, ReadTimeout, ConnectError

from com import father
from com.gheaders.log import LoggerClass

logger = LoggerClass('debug')


class GetUpdate:
    def __init__(self):
        self.url = (
            "https://api.telegram.org" if father.AdReg.get('Proxy')['TG_API_HOST'] == "" else father.AdReg.get('Proxy')['TG_API_HOST'])
        self.Token = "/bot" + father.AdReg.get('Token')
        self.headers = {"Content-Type": "application/json",
                        "Connection": "close",
                        }
        self.data = {
            "offset": 0,
            "timeout": 100
        }
        self.proxies = father.AdReg.get('Proxy')['Proxy'] if father.AdReg.get('Proxy')['Proxy'] else None
        self.Send_IDs = father.AdReg.get('Send_IDs')  # 要转发到群或者频道ID

    def get_long_link(self, ti=99):
        """
        长链接
        :param ti: 最大请求时间
        :return: 失败返回 {"ok": False,"result": []}
        """
        try:
            with httpx.Client(base_url=self.url, proxies=self.proxies) as client:
                ur = client.get(
                    f"{self.Token}/getUpdates?offset={self.data['offset']}&timeout={ti}&allowed_updates=['callback_query']",
                    timeout=ti)
                ur.close()
                # 如果是200表示收到消息
                if ur.status_code == 200:
                    js = ur.json()
                    if 'ok' in js:
                        return js
                # 502 和409表示没有消息
                elif ur.status_code == 502 or ur.status_code == 409:
                    return {"ok": True, "result": []}
                elif ur.status_code == 404:
                    return {"ok": False, "result": [f'404: {ur.text}']}
                else:
                    # 遇到其他未知状态码打印出来
                    return {"ok": False, "result": [ur.status_code]}
        except RemoteProtocolError:
            return {"ok": True, "result": []}
        except ConnectTimeout as e:
            return {"ok": False,
                    "result": [f"链接网络异常请确保服务器网络可以访问https://api.telegram.org 官方异常信息: {e}"]}
        except ReadTimeout:
            return {"ok": True, "result": []}
        except ConnectError:
            return {"ok": True, "result": []}
        except Exception as e:
            return {"ok": False, "result": [e]}

    def send_message(self, text, chat_id=None):
        """
        发送消息
        :return:
        """
        try:
            with httpx.Client(base_url=self.url, proxies=self.proxies) as client:
                ur = client.post(f'{self.Token}/sendMessage',
                                 data={"chat_id": chat_id, "text": text})
                js = ur.json()
                if ur.status_code == 200:
                    return 0
                elif ur.status_code == 403:
                    logger.write_log(f"转发消息失败，机器人不在你转发的频道或者群组\n失败原因{js['description']}")
                elif ur.status_code == 400:
                    logger.write_log(f"转发消息失败，可能问题权限不足\n失败原因{js['description']}")
                else:
                    logger.write_log(f"转发消息失败\n状态码{js['error_code']}\n失败原因{js['description']}")
                return -1
        except Exception as e:
            logger.write_log(f"发送消息异常: {e}")
            return -1
        finally:
            client.close()

    def leaveChat(self, chat_id):
        """
        使用此方法让您的机器人离开组、超级组或频道。成功返回True
        :return:
        """
        try:
            with httpx.Client(base_url=self.url, proxies=self.proxies) as client:
                ur = client.post(f'{self.Token}/sendMessage',
                                 data={"chat_id": chat_id})
                js = ur.json()
                client.close()
                if father.AdReg.get('Administrator'):
                    if ur.status_code == 200 and js['ok']:
                        self.send_message(f"退出 {chat_id} 群聊成功", father.AdReg.get('Administrator'))
                        return 0
                    else:
                        self.send_message(f"退出 {chat_id} 失败 {js['description'] if 'description' in js else ''}",
                                          father.AdReg.get('Administrator'))
                        return 400
                else:
                    return 404
        except Exception as e:
            return -1
