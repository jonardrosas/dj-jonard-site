import requests
import os
from django.conf import settings

class PorkbunDomainBase:

    def __init__(self):
        self.apikey = settings.PORKBUN_APIKEY
        self.secretapikey = settings.PORKBUN_SECRETAPIKEY
        self.base_url = "https://api.porkbun.com/api/json/v3"

    def list_domains(self):
        url = f"{self.base_url}/domain/listAll"
        data = {
            'secretapikey': self.secretapikey,
            'apikey': self.apikey,
            "start": "0",
            "includeLabels": "yes"
        }
        resp = requests.post(url, json=data)
        domains = resp.json().get('domains', [])
        return domains


    def get_ssl(self, domain):
        url = f"{self.base_url}/ssl/retrieve/{domain}"
        data = {
            'secretapikey': self.secretapikey,
            'apikey': self.apikey,
        }
        resp = requests.post(url, json=data)
        return resp.json()




def get_ssl():
    porkbun = PorkbunDomainBase()
    domains = porkbun.list_domains()
    for domain in domains:
        name = domain["domain"]
        porkbun_ssl = porkbun.get_ssl(name)
        keys = {
            "certificatechain": "domain.cert.pem",
            "privatekey": "private.key.pem",
            "publickey": "public.key.pem"
        }
        for k, filename in keys.items():
            file_path = settings.BASE_DIR / "ssl" / name / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                contents = porkbun_ssl.get(k)
                file.write(contents)