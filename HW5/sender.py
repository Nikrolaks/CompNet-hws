import socket
import ssl
import os

from enum import Enum

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import base64

LOGIN = "kopeikina.sofya"
SENDER_EMAIL = LOGIN + "@gmail.com"
SERVER = "smtp.gmail.com"
PORT = 587

class MSGType(Enum):
    string = 1
    html = 2


ERROR_MSG = "There are some troubles... Server didn't send required reply after "
def check_reply(smtp_socket, code, action):
    reply = ""
    while True:
        reply = smtp_socket.recv(2048)
        reply = reply.decode()
        if len(reply) == 0:
            continue
        if len(reply) < 3 or reply[:3] != str(code):
            raise RuntimeError(ERROR_MSG + action + "\r\nHe replied: " + reply)
        print("Server replied: " + reply)
        return


def sender(recepient, subject, msg_entry, msg_type:MSGType, attachement=""):
    smtp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    smtp_socket.connect((SERVER, PORT))
    check_reply(smtp_socket, 220, "CONNECTION TRY")

    ehlo = "EHLO " + LOGIN + ".gmail.com\r\n"
    smtp_socket.send(ehlo.encode())
    check_reply(smtp_socket, 250, "IDENTIFY TRY")

    start_tls = "STARTTLS\r\n"
    smtp_socket.send(start_tls.encode())
    check_reply(smtp_socket, 220, "STARTTLS")

    with ssl.create_default_context().wrap_socket(smtp_socket, server_hostname=SERVER) as ssock:
        auth_login = "AUTH LOGIN\r\n"
        ssock.send(auth_login.encode())
        check_reply(ssock, 334, "AUTH LOGIN")

        login = base64.b64encode(bytes(SENDER_EMAIL, "utf-8")).decode("utf-8") + "\r\n"
        ssock.send(login.encode())
        check_reply(ssock, 334, "SENDING LOGIN")

        pwd = base64.b64encode(bytes(os.environ["API_SECRET"], "utf-8")).decode("utf-8") + "\r\n"
        ssock.send(pwd.encode())
        check_reply(ssock, 235, "SENDING AUTH DATA")

        mail_from = "MAIL FROM:<" + SENDER_EMAIL + ">\r\n"
        ssock.send(mail_from.encode())
        check_reply(ssock, 250, "SET SENDER")

        rcpt_to = "RCPT TO:<" + recepient + ">\r\n"
        ssock.send(rcpt_to.encode())
        check_reply(ssock, 250, "SET RECEPIENT")

        ssock.send("DATA\r\n".encode())
        check_reply(ssock, 354, "START SENDING DATA")

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recepient
        msg["Subject"] = subject

        if msg_type == MSGType.string:
            msg.attach(MIMEText(msg_entry))
        else:
            msg.attach(MIMEText(msg_entry, "html"))

        if attachement != "":
            msg.attach(MIMEImage(attachement))

        data = msg.as_string() + "\r\n.\r\n"
        ssock.sendall(data.encode())
        check_reply(ssock, 250, "SENDING MAIL")

        quit = "QUIT\r\n"
        ssock.send(quit.encode())
        check_reply(ssock, 221, "QUIT")
    
if __name__ == "__main__":
    with open("mini.png", "rb") as file:
        sender("st088166@student.spbu.ru", "LAB 05 try billion two again (3)", "Recieve my mini image pls", MSGType.string, attachement=file.read())
