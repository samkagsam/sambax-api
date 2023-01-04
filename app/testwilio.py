# Download the helper library from https://www.twilio.com/docs/python/install
import os
from .config import settings
from twilio.rest import Client


# Set environment variables for your credentials
# Read more at http://twil.io/secure
account_sid = settings.twilio_account_sid
auth_token = settings.twilio_auth_token
client = Client(account_sid, auth_token)

message = client.messages.create(
  body="Your verification code is 7836.",
  from_="SAMBAX",
  to="+256705579354"
)

print(message.sid)