import requests
from requests.structures import CaseInsensitiveDict
import io
import random
import string
import time
import cv2
import uuid
import os


async def create_multipart(data, fieldname, filename, content_type):
    """
    Basic emulation of a browser's multipart file upload
    """
    print('---Generating multipart---')
    boundry = '------WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
    buff = io.BytesIO()

    buff.write(boundry.encode())
    buff.write(b'\r\n')
    buff.write(('Content-Disposition: form-data; name="%s"; filename="%s"' % \
                (fieldname, filename)).encode())
    buff.write(b'\r\n')
    buff.write(('Content-Type: %s' % content_type).encode())
    buff.write(b'\r\n')
    buff.write(b'\r\n')
    buff.write(data)
    buff.write(b'\r\n')
    buff.write(boundry.encode())
    buff.write(b'--\r\n')
    headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundry}
    headers['Content-Length'] = str(buff.tell())
    return buff.getvalue(), headers


async def get_anon_token():
    print('---Getting anonymous token---')
    url = "https://cclight-transient-user.adobe.io/users/anonymous_token"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "*/*"
    headers["Accept-Language"] = "en-US,en;q=0.9,ru;q=0.8,fr;q=0.7"
    headers["Connection"] = "keep-alive"
    headers["Content-Length"] = "0"
    headers["Origin"] = "https://express.adobe.com"
    headers["Referer"] = "https://express.adobe.com/"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "cross-site"
    headers[
        "User-Agent"] = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Mobile Safari/537.36 Edg/103.0.1264.71"
    headers["X-Api-Key"] = "MarvelWeb3"
    headers["sec-ch-ua"] = '" Not;A Brand";v="99", "Microsoft Edge";v="103", "Chromium";v="103"'
    headers["sec-ch-ua-mobile"] = "?1"
    headers["sec-ch-ua-platform"] = '"Android"'

    resp = requests.post(url, headers=headers)
    print(resp.headers)
    anon = resp.json()['access_token']
    print(resp.status_code)
    return anon


async def upload_file(init_headers, data_raw, anon):
    print('---Uploading image---')
    url = "https://cclight-transient-user.adobe.io/assets/upload"
    init_headers["Content-Type"] = init_headers["Content-Type"].replace('------', '----', 1)
    headers = CaseInsensitiveDict()
    headers["Accept"] = "*/*"
    headers["Accept-Language"] = "en-US,en;q=0.9,ru;q=0.8,fr;q=0.7"
    headers["Accept-Encoding"] = "gzip, deflate, br"
    headers["Connection"] = "keep-alive"
    headers["Content-Type"] = init_headers["Content-Type"]
    headers["Content-Length"] = init_headers["Content-Length"]
    headers["Origin"] = "https://express.adobe.com"
    headers["Referer"] = "https://express.adobe.com/"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "cross-site"
    headers[
        "User-Agent"] = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Mobile Safari/537.36 Edg/103.0.1264.71"
    headers["X-Api-Key"] = "MarvelWeb3"
    headers["sec-ch-ua"] = '" Not;A Brand";v="99", "Microsoft Edge";v="103", "Chromium";v="103"'
    headers["sec-ch-ua-mobile"] = "?1"
    headers["sec-ch-ua-platform"] = '"Android"'
    headers[
        "x-anonymous-auth"] = f"Bearer {anon}"

    resp = requests.post(url, headers=headers, data=data_raw)

    print(resp.status_code)
    print(resp.headers)
    print(resp.content)
    print(resp.json()['items'][0])
    return resp.json()['items'][0]


async def request_mask(mask, anon):
    print('---Requesting mask---')
    url = f"https://cclight-transient-user.adobe.io/mask/{mask}"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "*/*"
    headers["Accept-Language"] = "en-US,en;q=0.9,ru;q=0.8,fr;q=0.7"
    headers["Connection"] = "keep-alive"
    headers["Content-Length"] = "0"
    headers["Origin"] = "https://express.adobe.com"
    headers["Referer"] = "https://express.adobe.com/"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "cross-site"
    headers[
        "User-Agent"] = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Mobile Safari/537.36 Edg/103.0.1264.71"
    headers["X-Api-Key"] = "MarvelWeb3"
    headers["sec-ch-ua"] = '" Not;A Brand";v="99", "Microsoft Edge";v="103", "Chromium";v="103"'
    headers["sec-ch-ua-mobile"] = "?1"
    headers["sec-ch-ua-platform"] = '"Android"'
    headers[
        "x-anonymous-auth"] = f"Bearer {anon}"

    resp = requests.post(url, headers=headers)
    print(resp.status_code)
    print(resp.headers)
    print(resp.content)
    new_mask_id = resp.json()['mask_id']
    time.sleep(10)
    print('---Getting mask---')
    url = f"https://cclight-transient-user.adobe.io/mask/status/{new_mask_id}"
    resp = requests.get(url, headers=headers)
    print(resp.status_code)
    print(resp.headers)
    print(resp.content)
    print(resp.json())
    return resp.json()['_links']['download']['uri']


async def generate_final_image(image_path, mask_path):
    # load images
    img_org = cv2.imread(image_path)
    img_mask = cv2.imread(mask_path)
    unique_filename = str(uuid.uuid4())

    # convert colors
    # img_org  = cv2.cvtColor(img_org, ???)
    img_mask = cv2.cvtColor(img_mask, cv2.COLOR_BGR2GRAY)

    # add alpha channel
    b, g, r = cv2.split(img_org)
    img_output = cv2.merge([b, g, r, img_mask], 4)

    # write as png which keeps alpha channel
    cv2.imwrite(f'output/{unique_filename}.png', img_output)



