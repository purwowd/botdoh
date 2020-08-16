from flask import Flask, request
from flask_mysqldb import MySQL
from time import sleep

import telegram
import requests
import emoji
import json
import re

from app import config


global bot
global TOKEN

FPATH = config.FILE_PATH
TOKEN = config.BOT_TOKEN
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/{}'.format(TOKEN), methods=['POST'])
def main():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.effective_message.chat.id
    msg_id = update.effective_message.message_id
    date = update.effective_message.date
    sender = update.effective_message.from_user.username
    text = update.effective_message.text.encode('utf-8').decode()

    datetime = date.strftime('%d/%m/%Y %H:%M:%S')

    print('=> FROM: @' + sender + ' - - [' + datetime + '] "MESSAGE: "' + text + '" <=')

    # Check text is emoticon (emoji) or not
    text = emoji.demojize(text)

    if text == '/start':
        msg = "Halo, saya adalah @botdohkali_bot🤖"
        bot.sendChatAction(chat_id=chat_id, action='typing')
        sleep(1.5)
        bot.sendMessage(chat_id=chat_id, text=msg, reply_to_message_id=msg_id)
        return 'ok'
    elif '/picme ' in text:
        text = text[7:]
        try:
            text = re.sub(r'w', '_', text)
            photo = 'https://api.adorable.io/avatars/285/{}.png'.format(text.strip())
            bot.sendChatAction(chat_id=chat_id, action='upload_photo')
            sleep(2)
            bot.sendPhoto(chat_id=chat_id, photo=photo, reply_to_message_id=msg_id)
        except Exception:
            bot.sendChatAction(chat_id=chat_id, action='typing')
            sleep(1.5)
            bot.sendMessage(chat_id=chat_id, text="Maaf, nama kamu terlalu keren sekali 👀")
        return 'ok'
    elif text[0] == ':':
        msg = "Maaf, pesan tidak boleh hanya menggunakan emoticon (emoji) atau diawali dengan emoticon (emoji)."
        bot.sendChatAction(chat_id=chat_id, action='typing')
        sleep(1.5)
        bot.sendMessage(chat_id=chat_id, text=msg, reply_to_message_id=msg_id)
        return 'ok'
    elif text[0] == '0' and len(text) == 12:
        text = text[1:]
        with open(config.FILE_PATH + config.FILENAME, 'r') as file:
            for line in file:
                if text in line:
                    parse = line.rstrip('\n').replace('|', ',').split(',')
                    imsi = "📍 *IMSI:* " + parse[0]
                    msisdn = "📞 *MSISDN:* 0" + parse[1]
                    operator = "📡 *Operator:* " + parse[3]
                    msg = msisdn + "\n" + imsi + "\n" + operator + "\n"
                    bot.sendChatAction(chat_id=chat_id, action='typing')
                    sleep(1.5)
                    bot.sendMessage(
                        chat_id=chat_id,
                        text=msg,
                        reply_to_message_id=msg_id,
                        parse_mode='Markdown'
                    )
                    return 'ok'
                    break
                elif text[1] == '3' or text[1] == '7':
                    cur = mysql.connection.cursor()
                    cur.execute(config.QUERY + text)
                    datas = cur.fetchall()
                    obj = json.dumps(datas)
                    datas = json.loads(obj)

                    for data in datas:
                        imsi = "📍 *IMSI:* " + data['imsi']
                        msisdn = "📞 *MSISDN:* 0" + data['msisdn']
                        imei = "📌 *IMEI:* " + data['imei']
                        brand = "💎 *Brand:* " + data['brand']
                        operator = "📡 *Operator:* " + data['operator']
                        msg = msisdn + "\n" + imei + "\n" + imsi + "\n" + brand + "\n" + operator
                        bot.sendChatAction(chat_id=chat_id, action="typing")
                        sleep(1.5)
                        bot.sendMessage(
                            chat_id=chat_id,
                            text=msg,
                            reply_to_message_id=msg_id,
                            parse_mode='Markdown'
                        )
                        return 'ok'
                        break
                    else:
                        bot.sendChatAction(chat_id=chat_id, action="typing")
                        sleep(1.5)
                        bot.sendMessage(chat_id=chat_id, text="Maaf, data tidak ada.")
                        return 'ok'
            else:
                bot.sendChatAction(chat_id=chat_id, action="typing")
                sleep(1.5)
                bot.sendMessage(chat_id=chat_id, text="Maaf, data tidak ada.")
                return 'ok'
        file.close()
        sleep(1)
        return 'ok'
    else:
        url = config.BOT_API_URL
        payload = {"utext": text, "lang": "id"}
        headers = {"content-type": "application/json", "x-api-key": config.BOT_API_KEY}
        res = requests.request('POST', url, json=payload, headers=headers)
        msg = json.loads(res.text)

        try:
            msg = msg['atext']
            names = config.BOT_NAME

            for name in names:
                if name in msg:
                    msg = msg.replace(name, '@botdohkali_bot🤖')

            bot.sendChatAction(chat_id=chat_id, action="typing")
            sleep(1.5)
            bot.sendMessage(chat_id=chat_id, text=data)
        except KeyError:
            bot.sendChatAction(chat_id=chat_id, action="typing")
            sleep(1.5)
            bot.sendMessage(
                chat_id=chat_id,
                text="Maaf, waktu ngobrolku sudah habis, ☹️😔 \nSampai ketemu besok ya... 😊"
            )

        return 'ok'


@app.route('/hook', methods=['GET', 'POST'])
def hook():
    set_hook = bot.setWebhook('{URL}{HOOK}'.format(URL=config.URL_HOOK, HOOK=TOKEN))

    if set_hook:
        return 'success'
    else:
        return 'failed!'


@app.route('/')
def index():
    return '<p>It works!</p>'


if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True)
