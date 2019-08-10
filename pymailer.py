import socket
import ssl
import os
import json
from argparse import ArgumentParser, RawTextHelpFormatter
from email.message import EmailMessage
from mimetypes import MimeTypes
from base64 import b64encode

class Mailer:

  def __init__(self, hostname, port):
    self.hostname = hostname
    self.port = port
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket = ssl.create_default_context().wrap_socket(self.s, server_hostname=hostname)
    
  def login(self, username, password):
    self.username = b64encode(username.encode()) + b"\r\n"
    self.password = b64encode(password.encode()) + b"\r\n"
    
    if self.port == 587:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.hostname, self.port))
        response = self.socket.recv(1024).decode()
        print(response.strip("\r\n"))
        if response[:3] == "220":
            self.socket.send(b"HELO relay.pymailer.com\r\n")
            response = self.socket.recv(1024).decode()
            print(response.strip("\r\n"))
            if response[:3] == "250":
                self.socket.send(b"STARTTLS\r\n")
                while True:
                    response = self.socket.recv(1024).decode()
                    print(response.strip("\r\n"))
                    if response[:9] == "220 2.0.0":
                        self.socket = ssl.create_default_context().wrap_socket(self.socket, server_hostname=self.hostname)
                        self.socket.send(b"HELO relay.pymailer.com\r\n")
                        response = self.socket.recv(1024).decode()
                        print(response.strip("\r\n"))
                        self.socket.send(b"AUTH LOGIN\r\n")
                    if response[:16] == "334 VXNlcm5hbWU6":
                        self.socket.send(self.username)
                    if response[:16] == "334 UGFzc3dvcmQ6":
                        self.socket.send(self.password)
                    if response[:3] == "235":
                        return True
                    if response[:3] == "535":
                        self.socket.shutdown(socket.SHUT_RDWR)
                        return False

    elif self.port == 465:
        self.socket.connect((self.hostname, self.port))

        while True:
            response = self.socket.recv(1024).decode()
            print(response.strip("\r\n"))
            if response[:3] == "220":
                self.socket.send(b"HELO relay.pymailer.com\r\n")
            if response[:3] == "250":
                self.socket.send(b"AUTH LOGIN\r\n")
            if response[:16] == "334 VXNlcm5hbWU6":
                self.socket.send(self.username)
            if response[:16] == "334 UGFzc3dvcmQ6":
                self.socket.send(self.password)
            if response[:3] == "235":
                return True
            if response[:3] == "535":
                self.socket.shutdown(socket.SHUT_RDWR)
                return False

  def send(self, sender, recip, subject, message, attachment=False):
    
    myorigin = f"MAIL FROM:<{sender}>\r\n"
    mydest = f"RCPT TO:<{recip}>\r\n"
    msg = EmailMessage()
    msg["To"] = recip
    msg["From"] = sender
    msg["Subject"] = subject
    msg.set_content(message)
    self.socket.send(myorigin.encode())
    
    if attachment != False:
        with open(attachment, "rb") as f:
            data = f.read()
            mimetype = MimeTypes().guess_type(attachment)[0]
            maintype, subtype = mimetype.split("/")
            msg.add_attachment(data, maintype=mimetype, subtype=subtype, filename=os.path.basename(attachment))
            msg = str(msg) + "\r\n.\r\n"
        while True:
            response = self.socket.recv(1024).decode()
            print(response.strip("\r\n"))
            if response[:9] == "250 2.1.0":
                self.socket.send(mydest.encode())
            if response[:9] == "250 2.1.5":
                self.socket.send(b"DATA\r\n")
            if response[:3] == "354":
                self.socket.send(msg.encode())
            if response[:3] == "250" and response[:9] != "250 2.1.0" and response[:9] != "250 2.1.5":
                self.socket.send(b"QUIT\r\n")
                if self.socket.recv(1024).decode()[:3] == "221":
                    self.socket.shutdown(socket.SHUT_RDWR)
                    return True
    else:
        msg = str(msg) + "\r\n.\r\n"
        while True:
            response = self.socket.recv(1024).decode()
            print(response.strip("\r\n"))
            if response[:9] == "250 2.1.0":
                self.socket.send(mydest.encode())
            if response[:9] == "250 2.1.5":
                self.socket.send(b"DATA\r\n")
            if response[:3] == "354":
                self.socket.send(msg.encode())
            if response[:3] == "250" and response[:9] != "250 2.1.0" and response[:9] != "250 2.1.5":
                self.socket.send(b"QUIT\r\n")
                response = self.socket.recv(1024).decode()
                print(response.strip("\r\n"))
                if response[:3] == "221":
                    self.socket.shutdown(socket.SHUT_RDWR)
                    return True

if __name__ == "__main__":
    parser = ArgumentParser(description="PyMailer by Glitch\r\nReddit: https://www.reddit.com/user/vigilexe\r\nGithub: https://github.com/l337glitchl337\r\nEmail: glitchedwarlock@gmail.com", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-r", "--recipient", required=True, help="email address of recipient", metavar="", dest="recip")
    parser.add_argument("-s", "--sender", required=True, help="senders email", metavar="", dest="sender")
    parser.add_argument("-b", "--body", required=True, help="body of the message you would like to send", metavar="", dest="body")
    parser.add_argument("-a", "--attachment", help="path to file", metavar="", dest="attachment")
    parser.add_argument("-sbj", "--subject", help="subject of email", metavar="", dest="subject")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.0.1")
    args = parser.parse_args()
    recip = args.recip
    sender = args.sender
    subject = args.subject
    body = args.body.encode().decode("unicode_escape")

    with open("pymailer.config", "r") as f:
        creds = json.loads(f.read())
    
    if creds["email"] == "" or creds["password"] == "" or creds["smtpserver"] == "" or creds["port"] == "":
        print("Error, needed information not in pymailer.config")
        exit()
    
    mailer = Mailer(creds["smtpserver"], int(creds["port"]))
    status = mailer.login(creds["email"], creds["password"])

    if status == True:
        print("Login succesful")
    else:
        print("Error logging in")
        exit()

    if args.attachment:
        status = mailer.send(sender, recip, subject, body, attachment=args.attachment)
    else:
        status = mailer.send(sender, recip, subject, body)

    if status == True:
        print("Email sent")
    else:
        print("Email failed to deliver")