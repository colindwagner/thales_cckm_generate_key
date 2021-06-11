import requests
import json
import sys
from datetime import datetime

requests.urllib3.disable_warnings()
session = requests.Session()
session.verify = False

#enter cckm url here
cckm_url = "https://URL_HERE:8443/kmaas/"

resp = session.get(cckm_url)
now = datetime.now()
seconds = now.strftime("%s")  # seconds since epoch
expseconds = ((365 * 2) * 60) * 60
seconds = int(seconds)
exp = seconds + expseconds

# For Azure service principal login
# Replace your tenant name and tenant password
tenant = sys.argv[1]
password = sys.argv[2]
session.headers = {'X-XSRF-TOKEN': resp.headers['X-XSRF-TOKEN']}
data = {'tenant': tenant, 'password': password}
resp = session.post(cckm_url + "auth2/azure", data=data)

if resp.status_code != 200:
    print(resp.content)
    sys.exit()

session.headers['Content-Type'] = 'application/json'

def call_api(method, api, data=data):
    if method == 'post':
      resp = session.post(cckm_url + api, data=json.dumps(data))
    elif method == 'put':
      resp = session.put(cckm_url + api, data=data)
    else:
      resp = session.get(cckm_url + api)
      print("%s %s" % (method, api))
    if data:
      print(data)
      print(json.dumps(resp.json(), indent=4))
    return resp.json()


# Add a source key
new_source_key = sys.argv[4]

data = {"name": new_source_key , "algorithm": "RSA2048", "service": "Azure",
        "description": "automated generated key", "cckmId": "user" + tenant "}

call_api("post", "rest/keyvaultkey", data)

# Upload the new source key to Azure
# First search source key by name and find its ID
source_key = call_api("get", "rest/keyvaultkey/keys?search=%s" % new_source_key)
source_key_id = source_key['content'][0]['id']

# Prepare Azure key, replace with your key vault and key names
azure_key_vault = sys.argv[3]
data = {
    "keyVaultKeyId": source_key_id,
    "keyVaultName": azure_key_vault,
    "keyVaultDisplayName": azure_key_vault,
    "keyName": new_source_key,
    "attributes": {
    "enabled": True,
    "exp": exp
    },
    "hsm": False,
    "key_ops": ["encrypt"],
    "tags": {
    "tag1": "test tag"
    }
}
call_api("post", "rest/azureKeys/upload", data)
# Find Azure key by name
azure_key = call_api("get", "rest/azureKeys/search/findByName?name=%s" % new_source_key )

resp = session.post(cckm_url + "logout")
