"""
ATM客户端 — 符合 RFC-20242024 协议
模拟ATM终端，与银行服务器进行通信
用法: python client.py [serverIP] [port]
默认: 127.0.0.1 2525
"""

import socket
import sys


# ==================== 常量定义 ====================
DEFAULT_HOST = "172.20.10.3"
DEFAULT_PORT = 17685
BUFFER_SIZE  = 1024


# ==================== 命令行参数解析 ====================
def parse_args():
    server_ip = DEFAULT_HOST
    port      = DEFAULT_PORT

    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
            if port < 1 or port > 65535:
                print(f"端口号范围应为 1~65535，将使用默认端口 {DEFAULT_PORT}")
                port = DEFAULT_PORT
        except ValueError:
            print(f"无效的端口号，将使用默认端口 {DEFAULT_PORT}")

    return server_ip, port


# ==================== 网络通信基础函数 ====================
def send_line(sock, message):
    """发送一行命令（自动加换行符）"""
    data = (message + "\n").encode("utf-8")
    sock.sendall(data)
    print(">>>", message)

def recv_line(sock):
    """接收一行响应"""
    data = sock.recv(BUFFER_SIZE)
    if not data:
        return ""
    return data.decode("utf-8").strip()


# ==================== 主函数 ====================
def main():
    server_ip, port = parse_args()

    print("=" * 50)
    print("ATM客户端启动（RFC-20242024）")
    print(f"服务器地址: {server_ip}:{port}")
    print("=" * 50)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("\n正在连接服务器...")
        sock.connect((server_ip, port))
        print("已连接到ATM服务器 " + server_ip + ":" + str(port))

        # === 插卡 ===
        card_no = input("请输入卡号: ").strip()
        if not card_no:
            print("卡号不能为空！")
            return

        send_line(sock, f"HELO {card_no}")
        response = recv_line(sock)
        print("服务器响应:", response)

        if not response.startswith("500"):
            print("服务器错误: " + response)
            return

        # === 验证口令 ===
        print("服务器要求验证口令: " + response)
        passwd = input("请输入口令: ").strip()
        if not passwd:
            print("口令不能为空！")
            return

        send_line(sock, f"PASS {passwd}")
        response = recv_line(sock)
        print("服务器响应:", response)

        if response != "525 OK!":
            print("认证失败: " + response)
            return

        print("认证成功！")

        # === 主菜单循环 ===
        while True:
            print("\n" + "=" * 40)
            print("        银行服务菜单")
            print("=" * 40)
            print("  1. 查询账户余额  (BALA)")
            print("  2. 取款           (WDRA)")
            print("  3. 退出服务       (QUIT)")
            print("=" * 40)

            choice = input("请选择操作 [1/2/3]: ").strip()

            if choice == "1" or choice.upper() == "BALA":
                send_line(sock, "BALA")
                response = recv_line(sock)
                print("服务器响应:", response)
                if response.startswith("AMNT:"):
                    print("当前余额: " + response[5:] + " 元")
                elif response == "401 ERROR!":
                    print("查询失败")

            elif choice == "2" or choice.upper() == "WDRA":
                amount_input = input("请输入取款金额: ").strip()
                if not amount_input:
                    print("金额不能为空！")
                    continue
                send_line(sock, f"WDRA {amount_input}")
                response = recv_line(sock)
                print("服务器响应:", response)
                if response == "525 OK!":
                    print("取款成功！")
                elif response == "401 ERROR!":
                    print("取款失败（余额不足或金额无效）")

            elif choice == "3" or choice.upper() == "QUIT":
                send_line(sock, "QUIT")
                response = recv_line(sock)
                print("服务器响应:", response)
                if response == "BYE":
                    print("会话正常结束")
                break

            else:
                print("无效选择，请重新输入！")

    except socket.error as e:
        print("连接失败:", str(e))
        print("请确保服务器已启动并监听端口 " + str(port))
    finally:
        try:
            sock.close()
            print("\n连接已关闭")
        except:
            pass


if __name__ == "__main__":
    main()
