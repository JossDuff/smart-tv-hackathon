import asyncio, sys, json
sys.path.insert(0, '/home/joss/.local/share/pipx/venvs/mrg-iot/lib/python3.14/site-packages')
from mrg_iot.core.api import mergetb_client as mc

tok = json.load(open('/home/joss/.mrg-iot/session.json'))
key = asyncio.run(mc.get_ssh_key(tok['token'], tok['username']))
key.write_private_key_file('/home/joss/.ssh/mrg_xdc_key')
with open('/home/joss/.ssh/mrg_xdc_key.pub', 'w') as f:
    f.write(f'{key.get_name()} {key.get_base64()} mrg-iot\n')
print('key saved, bits:', key.get_bits())
