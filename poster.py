from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request, redirect
from threading import Lock
import json
import time
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./upload"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def render_poster(user_img_file, front_img_file, output_png, user):
    user_img = Image.open(user_img_file)
    front_img = Image.open(front_img_file)

    if user_img.size[0] > user_img.size[1]:
       sz = (front_img.size[1]/user_img.size[1]*user_img.size[0], front_img.size[1])
    else:
       sz = (front_img.size[0], front_img.size[0]/user_img.size[0]*user_img.size[1])
    sz = (int(sz[0]), int(sz[1]))
    user_img = user_img.resize(sz)
    user_img = user_img.crop((0,0,front_img.size[0], front_img.size[1]))
    user_img = user_img.convert("I").convert("RGBA")

    img = Image.alpha_composite(user_img, front_img)
    W, H = img.size

    code_img = Image.open('QRcode.png')
    img.paste(code_img, (0,0))

    # 加字

    d = ImageDraw.Draw(img)

    fnt = ImageFont.truetype('msyhbd.ttc', 56)
    d.text((7/100*W, 84.5/100*H), user['name'], font=fnt, fill=(255,255,255))

    fnt = ImageFont.truetype('msyhbd.ttc', 56)
    if len(user['en_name']) > 13:
        fnt = ImageFont.truetype('msyhbd.ttc', 48)
    d.text((7/100*W, 90/100*H), user['en_name'], font=fnt, fill=(0,0,0))


    fnt = ImageFont.truetype('msyhbd.ttc', 46)
    text_sz = fnt.getsize(user['title'])
    d.text((93.5/100*W-text_sz[0], 80.5/100*H-text_sz[1]/2), user['title'], font=fnt, fill=(255,255,255))


    fnt = ImageFont.truetype('msyhbd.ttc', 66)
    text_sz = fnt.getsize(user['motto'])
    d.text((40/100*W, 88.5/100*H-text_sz[1]/2), user['motto'], font=fnt, fill=(255,255,255))

    img.save(output_png, "png")


SAVE_USER_INFO_LOCK = Lock()
def save_user_info(user):
    with SAVE_USER_INFO_LOCK:
        with open('./user_info.txt', 'a') as f:
            f.write(json.dumps(user) + "\n")

def allowed_file(filename):
    ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def hello():
    return app.send_static_file('index.html')

    
@app.route("/gen_poster",  methods=['POST'])
def gen_poster():
    user = {
        'name': request.form['name'],
        'en_name': request.form['en_name'],
        'title': request.form['title'],
        'motto': '"请支持我成为TEDx讲者。"', # '"' + request.form['motto'] + '"',
    }
    if len(user['name']) > 6:
        return "名字过长"
    if len(user['en_name']) > 20:
        return "英文名过长"
    if len(user['title']) > 30:
        return "个人标签过长"    
    if len(user['motto']) > 50: 
        return "座右铭过长"    

    user_img_file = 'default-photo.png'
    front_img_file = 'front.png'
    output_png = './static/poster/' + str(time.time()) + '.png'

    if 'photo' in request.files:
        photo_file = request.files['photo']
        if photo_file:
            if not allowed_file(photo_file.filename):
                return "上传文件仅允许 png jpg jpeg" 
            file_name = str(time.time()) + "." + photo_file.filename.split(".")[-1]
            user_img_file = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            photo_file.save(user_img_file)

    user['photo'] = user_img_file
    user['poster'] = output_png
    user['ip'] = request.remote_addr
    save_user_info(user)
    render_poster(user_img_file, front_img_file, output_png, user)
    return """
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
	<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
	<!-- <script src="https://cdn.jsdelivr.net/npm/vue"></script> -->
	<link href="./static/semantic.min.css" rel="stylesheet">
	<script src="./static/semantic.min.js"></script>
	<title>TEDx讲者海报生成</title>
</head>
<body>
<div class="ui container" style="margin-top:30px">
    <div class="ui segment">
	<img src='{}' style='width:100%'>
<div class="ui one column centered grid" style="margin:7px 0 0 0">
    长按保存图片，分享给身边的朋友
</div>
    </div>
</div>
</body>
</html>
""".format(output_png)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=36666, debug=True, threaded=True)
    # app.run(host='0.0.0.0', debug=True)
