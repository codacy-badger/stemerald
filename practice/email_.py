import smtplib
from email.mime.multipart import MIMEMultipart

to = ''
host = ''
port = ''
username = ''
password = ''
local_hostname = ''
auth = True
ssl = False
tls = True

smtp_server = (smtplib.SMTP_SSL if ssl else smtplib.SMTP)(
    host=host,
    port=port,
    local_hostname=local_hostname
)
if tls:  # pragma: no cover
    smtp_server.starttls()

if auth:  # pragma: no cover
    smtp_server.login(username, password)

from_ = username

msg = MIMEMultipart()
msg['Subject'] = 'test'
msg['From'] = from_
msg['To'] = to
# if cc:
#     msg['Cc'] = cc
# if bcc:
#     msg['Bcc'] = bcc

smtp_server.send_message(msg)
smtp_server.quit()
