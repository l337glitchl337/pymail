import socket, ssl, os
from base64 import b64encode

class Mailer:

  def __init__(self, hostname, port):
    self.hostname = socket.gethostbyname(hostname)
    self.port = port
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket = ssl.create_default_context().wrap_socket(self.s, server_hostname=hostname)
    
  def login(self, username, password):
    self.username = b64encode(username.encode()) + b"\r\n"
    self.password = b64encode(password.encode()) + b"\r\n"
    self.socket.connect((self.hostname, self.port))

    while True:
      response = self.socket.recv(1024).decode()
      if response[:3] == "220":
        self.socket.send(b"HELO relay.example.com\r\n")
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
    msg = f"From: {sender}\r\nSubject: {subject}\r\nTo: {recip}\r\n{message}\r\n.\r\n"
    self.socket.send(myorigin.encode())

    if attachment != False:
        filename = os.path.basename(attachment)
        with open(filename, "rb") as f:
            data = b64encode(f.read()).decode()
            header = f"Content-Type: multipart/mixed; boundary=sep\r\n--sep\r\n{message}\r\n--sep\r\nContent--Type: application/octet-stream; name={filename}\r\nContent-Disposition: attachment; filename={filename}\r\nContent-Transfer-Encoding: base64\r\n{data}"
        msg = f"From: {sender}\r\nSubject: {subject}\r\nTo: {recip}\r\n{header}\r\n.\r\n"
        while True:
            response = self.socket.recv(1024).decode()
            if response[:12] == "250 2.1.0 OK":
                self.socket.send(mydest.encode())
            if response[:12] == "250 2.1.5 OK":
                self.socket.send(b"DATA\r\n")
            if response[:3] == "354":
                self.socket.send(msg.encode())
            if response[:12] == "250 2.0.0 OK":
                self.socket.send(b"QUIT\r\n")
                if self.socket.recv(1024).decode()[:9] == "221 2.0.0":
                    self.socket.shutdown(socket.SHUT_RDWR)
                    return True
    else:
        while True:
            response = self.socket.recv(1024).decode()
            if response[:12] == "250 2.1.0 OK":
                self.socket.send(mydest.encode())
            if response[:12] == "250 2.1.5 OK":
                self.socket.send(b"DATA\r\n")
            if response[:3] == "354":
                self.socket.send(msg.encode())
            if response[:12] == "250 2.0.0 OK":
                self.socket.send(b"QUIT\r\n")
                if self.socket.recv(1024).decode()[:9] == "221 2.0.0":
                    self.socket.shutdown(socket.SHUT_RDWR)
                    return True



if __name__ == "__main__":
    sender = input("Your Name: ")
    recip = input("Recipients email address: ")
    subject = input("Email subject: ")
    mlist = []
    print("Message body: ")
    while True:
        uinput = input()
        if uinput.lower() == "done":
            break
        mlist.append(uinput)
    yn = input("Attach a image?(y/n): ")
    if yn.lower() == "y":
        attachment = input("Path to image: ")
    message = "\r\n".join(mlist)
    mailer = Mailer("smtp.gmail.com", 465)
    result = mailer.login("<YOUR_EMAIL>", "<APP_PASSWORD>")
    if result == False:
        print("Error logging in..")
    else:
        if yn.lower() == "y":
            status = mailer.send(sender, recip, subject, message, attachment)
        else:
            status = mailer.send(sender, recip, subject, message)
        if status == True:
            print("Email sent.")
        else:
            print("Email failed to deliver.")
