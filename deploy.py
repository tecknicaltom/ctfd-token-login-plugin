from itsdangerous import URLSafeTimedSerializer
import glob
import os
import os.path
import re
import requests
import tarfile
import yaml
import optparse


parser = optparse.OptionParser(usage="Usage: %prog [options]")
parser.add_option('-d', dest='append_desciption')
(options, args) = parser.parse_args()

secret = os.getenv('CTFD_SECRET_KEY')
if not secret:
    raise ValueError('Environment variable CTFD_SECRET_KEY not found')

user = os.getenv('DEPLOYMENT_USER')
if not user:
    raise ValueError('Environment variable DEPLOYMENT_USER not found')

ctfd_domain = os.getenv('CTFD_DOMAIN')
if not ctfd_domain:
    raise ValueError('Environment variable CTFD_DOMAIN not found')


scoreboard_url_root = ctfd_domain
if not scoreboard_url_root.startswith('http'):
    scoreboard_url_root = 'https://' + ctfd_domain

serializer = URLSafeTimedSerializer(secret)
token = serializer.dumps(user)

s = requests.Session()
resp = s.post(scoreboard_url_root + '/api/token-login', json={'token': token})
resp.raise_for_status()

resp = s.get(scoreboard_url_root + '/admin/transfer')
resp.raise_for_status()
match = re.search(r'var csrf_nonce = "(?P<nonce>[a-f0-9]+)"', resp.text)
if not match:
    raise ValueError('CSRF nonce not found')
nonce = match.group('nonce')
print("extracted CSRF nonce: {}".format(nonce))

challenge_yaml = 'challenge.yaml'
print("Adding challenge yaml: {}".format(challenge_yaml))
additional_files = []
with open(challenge_yaml) as f:
    challenge_data = yaml.load(f.read())

    if options.append_desciption:
        challenge_data['description'] = "{}\n\n{}".format(challenge_data['description'].strip(), options.append_desciption)

    base = os.path.dirname(challenge_yaml)
    for filename in challenge_data.get('files', []):
        full_filename = os.path.join(base, filename)
        additional_files.append((full_filename, filename))

with open('export.yaml', 'w') as f:
    f.write(yaml.dump_all([challenge_data]))

with tarfile.open('export.tar.gz', "w:gz") as tar:
    tar.add('export.yaml')
    for name, arcname in additional_files:
        tar.add(name, arcname=arcname)

files = {'file': (
    'export.tar.gz',
    open('export.tar.gz', 'rb'),
    'application/x-gzip'
    )
}
resp = s.post(scoreboard_url_root + '/admin/yaml', files=files, data={'nonce': nonce})
resp.raise_for_status()
print("Success")
