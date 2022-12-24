from flask import Flask, request, send_file, after_this_request
import asyncio
import cv2
import uuid
import os
import filetype
from io import BytesIO
import os
import requests
from adobe import create_multipart, request_mask, get_anon_token, upload_file, generate_final_image
from PIL import Image

# Get The Current Directory
currentDir = os.path.dirname(__file__)

# Functions:
# Save Results

app = Flask(__name__)


@app.route("/removebg", methods=['POST'])
async def initiation_adobe():
    # try:
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    # Save input image
    uploaded_file.save(os.path.join(os.getcwd() + '/uploads', filename))

    # Check if webp uploaded as input
    if '.webp' in filename:
        im = Image.open(os.path.join(os.getcwd() + '/uploads', filename)).convert("RGB")
        os.remove(os.path.join(os.getcwd() + '/uploads', filename))
        filename = filename[:len(filename) - 4] + 'jpg'
        im.save(os.path.join(os.getcwd() + '/uploads', filename))

    # Reading data of image
    with open(os.path.join(os.getcwd() + '/uploads', filename), 'rb') as f:
        img_bytes = f.read()

    data, headers = await create_multipart(img_bytes, fieldname='file',
                                     filename='1.jpg',
                                     content_type='image/jpeg')

    anon = await get_anon_token()
    mask_id = await upload_file(headers, data, anon)
    download_link = await request_mask(mask_id, anon)

    img_data = requests.get(download_link).content

    # Save mask
    with open(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'), 'wb') as handler:
        handler.write(img_data)

    # Open image and mask
    img_org = cv2.imread(os.path.join(os.getcwd() + '/uploads', filename))
    img_mask = cv2.imread(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'))

    unique_filename = str(uuid.uuid4())

    # convert colors
    img_mask = cv2.cvtColor(img_mask, cv2.COLOR_BGR2GRAY)

    # add alpha channel
    b, g, r = cv2.split(img_org)
    img_output = cv2.merge([b, g, r, img_mask], 4)

    # write as png which keeps alpha channel
    cv2.imwrite(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), img_output)

    with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), 'rb') as file:
        result = file.read()

    # Delete all files generated
    os.remove(os.path.join(os.getcwd() + '/uploads', filename))
    os.remove(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'))

    # Send removed image
    with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), 'wb') as file:
        file.write(result)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'))
                file.close()
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response

    return send_file(
        os.path.join(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png')),
        mimetype='image/png')
    # except:
    #     return "{'result': 'invalid filetype'}", 500


@app.route("/removebgstatus", methods=['GET'])
def status():
    return {'status': 'ok'}


@app.route("/removebg", methods=['GET'])
async def initialize():
    try:
        file = str(request.args.get('file'))

        # if the url is given
        if 'http://' in file or 'https://' in file:
            unique_filename = str(uuid.uuid4())
            img_data = requests.get(file).content

            # Save image
            with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.jpg'), 'wb') as handler:
                handler.write(img_data)

            # with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.jpg'), 'rb') as f:
            #     img_bytes = f.read()

            data, headers = await create_multipart(img_data, fieldname='file',
                                             filename='1.jpg',
                                             content_type='image/jpeg')

            anon = await get_anon_token()
            mask_id = await upload_file(headers, data, anon)
            download_link = await request_mask(mask_id, anon)

            mask_data = requests.get(download_link).content

            with open(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'), 'wb') as handler:
                handler.write(mask_data)

            img_org = cv2.imread(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.jpg'))
            img_mask = cv2.imread(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'))

            # convert colors
            img_mask = cv2.cvtColor(img_mask, cv2.COLOR_BGR2GRAY)

            # add alpha channel
            b, g, r = cv2.split(img_org)
            img_output = cv2.merge([b, g, r, img_mask], 4)

            # write as png which keeps alpha channel
            cv2.imwrite(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), img_output)

            with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), 'rb') as file:
                result = file.read()

            os.remove(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.jpg'))
            os.remove(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'))

            with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), 'wb') as file:
                file.write(result)

                @after_this_request
                def remove_file(response):
                    try:
                        os.remove(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'))
                        file.close()
                    except Exception as error:
                        app.logger.error("Error removing or closing downloaded file handle", error)
                    return response

            return send_file(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'),
                             mimetype='image/png')
        else:
            unique_filename = str(uuid.uuid4())
            try:
                with open(file, 'rb') as f:
                    img_bytes = f.read()

            except:
                return "Cannot read file; Invalid path to the file or file does not exist", 500

            if '.webp' in file:
                im = Image.open(file).convert("RGB")
                file = file[:len(file) - 4] + 'jpg'
                im.save(file)
            with open(file,'rb') as f:
                img_bytes = f.read()
            data, headers = await create_multipart(img_bytes, fieldname='file',
                                             filename='1.jpg',
                                             content_type='image/jpeg')

            anon = await get_anon_token()
            mask_id = await upload_file(headers, data, anon)
            download_link = await request_mask(mask_id, anon)

            img_data = requests.get(download_link).content

            with open(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'), 'wb') as handler:
                handler.write(img_data)

            img_org = cv2.imread(file)
            img_mask = cv2.imread(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'))

            # convert colors
            # img_org  = cv2.cvtColor(img_org, ???)
            img_mask = cv2.cvtColor(img_mask, cv2.COLOR_BGR2GRAY)

            # add alpha channel
            b, g, r = cv2.split(img_org)
            img_output = cv2.merge([b, g, r, img_mask], 4)

            # write as png which keeps alpha channel
            cv2.imwrite(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), img_output)

            with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), 'rb') as file:
                result = file.read()

            # os.remove(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.jpg'))
            os.remove(os.path.join(os.getcwd() + '/uploads', 'adobe_mask.png'))

            with open(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'), 'wb') as file:
                file.write(result)

                @after_this_request
                def remove_file(response):
                    try:
                        os.remove(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'))
                        file.close()
                    except Exception as error:
                        app.logger.error("Error removing or closing downloaded file handle", error)
                    return response

            return send_file(os.path.join(os.getcwd() + '/uploads', f'{unique_filename}.png'),
                             mimetype='image/png')

    except:
        return {'result': 'error'}, 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
