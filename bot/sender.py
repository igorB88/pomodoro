# common
import json
import time
import pprint

# django
from django.conf import settings

# other
from pymessenger.bot import Bot
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove


class Button(object):
    def __init__(self, text, url=None, short_title=None, gallery=None, item=None, request_contact=False, data=None):
        self.text = text
        self.url = url
        self.request_contact = request_contact
        self.item = item
        self.short_title = short_title
        self.gallery = gallery
        self.data = data

    def fb_button(self):
        result = {
            'title': self.text,
        }
        if self.url:
            result['type'] = 'web_url'
            result['url'] = self.url
        else:
            result['type'] = 'postback'
            result['payload'] = self.payload

        return result

    @property
    def payload(self):
        data = {
            'text': self.text,
            'type': 'text',
        }
        return json.dumps(data)

    def __str__(self):
        return 'Button text: {}'.format(self.text)

    def __repr__(self):
        return self.__str__()


class Markup(object):
    def __init__(self, buttons=None, inline_buttons=None, remove_menu=False):
        self.buttons = buttons
        self.inline_buttons = inline_buttons
        self.remove_menu = remove_menu

    def to_telegram_markup(self):
        result = None
        if self.remove_menu:
            result = ReplyKeyboardRemove(remove_keyboard=True)
        elif self.buttons:
            keyboard = []
            for markup_row in self.buttons:
                row = []
                for markup_button in markup_row:
                    row.append(KeyboardButton(text=markup_button.text,
                                              request_contact=markup_button.request_contact))
                keyboard.append(row)
            result = ReplyKeyboardMarkup(keyboard=keyboard)
        elif self.inline_buttons:
            keyboard = []
            for markup_row in self.inline_buttons:
                row = []
                for markup_button in markup_row:
                    if markup_button.url:
                        row.append(InlineKeyboardButton(text=markup_button.text, url=markup_button.url))
                    elif markup_button.data:
                        callback = json.dumps(markup_button.data)
                        row.append(InlineKeyboardButton(text=markup_button.text, callback_data=callback))

                keyboard.append(row)
            result = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return result


class Sender(object):

    def __init__(self, social_platform, chat_id, msg_id=None, query_id=None):
        assert social_platform in ('telegram', 'facebook')
        self.social_platform = social_platform
        self.chat_id = chat_id
        self.msg_id = msg_id
        self.query_id = query_id

    def sendMessage(self, message, reply_markup=None, token=None):
        if self.social_platform == 'telegram':
            bot = telepot.Bot(token or settings.TELEGRAM_BOT_TOKEN)

            telegram_reply_markup = reply_markup.to_telegram_markup() if reply_markup else None
            bot.sendMessage(self.chat_id, message, reply_markup=telegram_reply_markup)
        elif self.social_platform == 'facebook':
            bot = Bot(settings.FACEBOOK_MESSENGER_ACCESS_TOKEN)

            if not reply_markup:
                result = bot.send_text_message(self.chat_id, message)
            elif reply_markup.remove_menu:
                result = bot.send_text_message(self.chat_id, message)
            elif reply_markup.buttons or reply_markup.inline_buttons:
                all_buttons = reply_markup.buttons or reply_markup.inline_buttons

                button_items = [b for row in all_buttons for b in row if b.item]
                tmp_buttons = [b for row in all_buttons for b in row if not b.item and not b.short_title and not b.gallery]
                other_buttons = tmp_buttons[3:]
                buttons = tmp_buttons[:3]
                short_titles = [b for row in all_buttons for b in row if b.short_title]
                gallery_items = [b for row in all_buttons for b in row if b.gallery]

                assert len(buttons) <= 3
                assert len(other_buttons) <= 3
                assert len(button_items) <= 4
                assert len(gallery_items) <= 10

                if button_items:
                    fb_buttons = [b.fb_button() for b in buttons]
                    elements = []
                    for button_item in button_items:
                        element = {
                            **button_item.item,
                        }
                        element["buttons"] = [{
                            "type": "postback",
                            "title": 'Select',
                            "payload": button_item.payload,
                        }]

                        elements.append(element)

                    data = {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "list",
                                "elements": elements,
                            }
                        }
                    }
                    result = bot.send_button_message(self.chat_id, message, buttons=fb_buttons)
                    result = bot.send_message(self.chat_id, data)
                elif gallery_items:
                    elements = []
                    for gallery_item in gallery_items:
                        element = {
                            **gallery_item.gallery,
                        }
                        if hasattr(gallery_item, 'buttons'):
                            element['buttons'] = [b.fb_button() for b in gallery_item.buttons]
                        else:
                            element['buttons'] = [{
                                'title': 'Select',
                                'type': 'postback',
                                'payload': gallery_item.payload,
                            }]
                        elements.append(element)

                    data = {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "generic",
                                "elements": elements,
                            }
                        }
                    }

                    fb_buttons = [b.fb_button() for b in buttons]
                    result = bot.send_button_message(self.chat_id, message, buttons=fb_buttons)

                    result = bot.send_message(self.chat_id, data)
                elif short_titles:
                    quick_replies = []
                    for button in short_titles:
                        quick_replies.append({
                            'content_type': 'text',
                            'title': button.short_title,
                            'payload': button.payload,
                        })

                    raw = {
                        'recipient': {
                            'id': self.chat_id,
                        },
                        'message': {
                            "text": message,
                            "quick_replies": quick_replies
                        }
                    }
                    result = bot.send_raw(raw)
                elif buttons:
                    fb_buttons = [b.fb_button() for b in buttons]
                    result = bot.send_button_message(self.chat_id, message, buttons=fb_buttons)

                if other_buttons:
                    fb_buttons = [b.fb_button() for b in other_buttons]
                    result = bot.send_button_message(self.chat_id, '...', buttons=fb_buttons)

            if 'error' in result:
                pprint.pprint(result)

    def editMessage(self, message, reply_markup=None, msg_id=None, token=None):
        if self.social_platform == 'telegram':
            bot = telepot.Bot(token or settings.TELEGRAM_BOT_TOKEN)
            telegram_reply_markup = reply_markup.to_telegram_markup() if reply_markup else None
            msg_id = tuple(msg_id or self.msg_id)   # should be tuple, telegram or telepot does not accept list
            bot.editMessageText(msg_id, message, reply_markup=telegram_reply_markup)

    def answer(self, message, token=None):
        if self.social_platform == 'telegram':
            bot = telepot.Bot(token or settings.TELEGRAM_BOT_TOKEN)
            bot.answerCallbackQuery(self.query_id, text=message)

    def sendPhoto(self, photo, caption=None, filename=None, token=None):
        if self.social_platform == 'telegram':
            bot = telepot.Bot(token or settings.TELEGRAM_BOT_TOKEN)
            filename = filename or f'unnamed{time.time()}.png'
            bot.sendPhoto(self.chat_id, (filename, photo), caption=caption)

    def sendAudio(self, audio, caption=None, token=None):
        if self.social_platform == 'telegram':
            bot = telepot.Bot(token or settings.TELEGRAM_BOT_TOKEN)
            bot.sendAudio(self.chat_id, audio, caption=caption)