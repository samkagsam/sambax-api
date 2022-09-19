import uuid
import requests

random_uuid = uuid.uuid4()
print(random_uuid)

url = "https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"
data = {
  "amount": "101",
  "currency": "{{currency}}",
  "externalId": "{{Payment-X-Reference-Id}}",
  "payer": {
    "partyIdType": "{{accountHolderIdTypeCaseUp}}",
    "partyId": "{{accountHolderId}}"
  },
  "payerMessage": "Test payment 2",
  "payeeNote": "Test payment 2"
}
#body = {"providerCallbackHost": "clinic.com"}
headers = {"X-Reference-Id": "2636c172-f78a-4f5a-afd1-5397bd15068f",
           "Ocp-Apim-Subscription-Key": "52f00c81a6ef44e29f9dd46951ed6698",
           "Content-type": "application/json",
           "X-Target-Environment":"sandbox",
           "Authorization":"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSMjU2In0.eyJjbGllbnRJZCI6IjIyMGM4YTQ0LWQzMmMtNGM1My1hZWY0LWIyMTcyMWQ3Zjc3ZiIsImV4cGlyZXMiOiIyMDIyLTA5LTA0VDE0OjM2OjM0Ljc5OSIsInNlc3Npb25JZCI6IjZiY2U1ZWQyLTQ1NjQtNGU1OC1hYTc5LTk2NjhiNzkxOTkyZCJ9.VU-ynYDIGSCGdRCs2yK7vqsaIxh_rfscZb5I4_dDKlk5mnnYN0ysmzi2HMMsL3q9wYo1vNkVEfQ18JH0z7y50lP8-PNzV2zv2-BCNlcFb7nCIBndH3_m7kuOaJUjTQLXaCw2R9D27G_TZoftE2Py0vF4JFLnZ4krmRsVZrK5KaiOXwnMxKHWr1nF3rTJSIpYaiV78yCaE4I1F3MYKA545mbxK-2uyNNBzzc8nk3735brUqPrOEksYrn2wz4CmUn0jSsF92Vy2pL0sFk5RYPi0GDSiYKv5HsSKDI9YAIklGG18PJhHbuvrkii_3O2U7VdFMoRJ2irXsET0Bq2mfhH6A"

           }
response = requests.post(url, data=data, headers=headers)

print(response.text)
print(response.status_code)
print(response.reason)
print(response.raise_for_status())
print(response.json())
