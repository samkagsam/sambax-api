# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Set environment variables for your credentials
# Read more at http://twil.io/secure
account_sid = "ACf3b2717f63d35e0b35e770fefccd9faf"
auth_token = "bc2487d1653d69076c8c49e02408c2bc"
client = Client(account_sid, auth_token)

message = client.messages.create(
  body="Join Earth's mightiest heroes. Like Kevin Bacon.",
  from_="+13344713159",
  to="+256705579354"
)

print(message.sid)