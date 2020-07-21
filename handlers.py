import config
from bot import ROMBot
from telebot import types
from datetime import datetime
from time import sleep

bot = ROMBot(config.TOKEN, config.API, config.URL, config.DB, config.H)


@bot.message_handler(commands=['start'])
def start(message):
    if bot.get_item_list() is None:
        bot.send_message(message.chat.id, 'Я не дошел до рынка, пойду спать..')
        bot.stop_polling()
    else:
        bot.send_message(message.chat.id, 'Я сходил на рынок, посмотрел что продают..')


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.chat.id, bot.get_help())


@bot.message_handler(commands=['find', 'f'])
def find_item(message):
    try:
        arg = message.text.split()[1:]
        if not arg:
            raise IndexError
    except IndexError:
        bot.send_message(message.chat.id, 'Что ищем то?')
    else:
        item_info = bot.find_item(' '.join(arg))
        bot.send_message(message.chat.id, item_info)
        bot.add_query_history(int(message.from_user.id), ' '.join(arg), int(message.date))


@bot.message_handler(commands=['history', 'h'])
def history_item(message):
    try:
        arg = message.text.split()[1:]
        if not arg:
            raise IndexError
    except IndexError:
        bot.send_message(message.chat.id, 'Что ищем то?')
    else:
        item_table = bot.history_item(' '.join(arg))
        if item_table is not None and len(item_table) > 0:
            bot.send_message(message.chat.id, item_table)
            bot.add_query_history(int(message.from_user.id), ' '.join(arg), int(message.date))
        else:
            bot.send_message(message.chat.id, 'Не могу найти')


@bot.inline_handler(func=lambda query: len(query.query) > 3)
def auto_fill(query):
    lines = bot.auto_fill(query.query)
    items = []
    for line in lines:
        items.append(types.InlineQueryResultArticle(id=line['id'],
                                                    title=line['title'],
                                                    description=line['description'],
                                                    input_message_content=types.InputTextMessageContent(
                                                        message_text=line['message_text'])
                                                    )
                     )
    bot.answer_inline_query(query.id, items)


@bot.inline_handler(func=lambda query: len(query.query) < 4)
def show_keyboard(query):
    keyboard = types.InlineKeyboardMarkup()
    for key in bot.get_query_history(query.from_user.id):
        keyboard.add(
            types.InlineKeyboardButton(text=f'[{datetime.fromtimestamp(key[2])}] {key[1]}', callback_data=key[1])
        )
    table = []
    msg = types.InlineQueryResultArticle(
        id='1', title='История поиска',
        input_message_content=types.InputTextMessageContent(message_text='История поиска:'),
        reply_markup=keyboard
    )
    table.append(msg)
    bot.answer_inline_query(query.id, table)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    bot.edit_message_text(inline_message_id=call.inline_message_id, text=bot.find_item(call.data))
    bot.add_query_history(int(call.from_user.id), call.data, datetime.now().timestamp())


@bot.message_handler(content_types=['text'])
def master(message):
    print(message)
    if message.text.lower() == 'валера' and message.from_user.id == config.MY_ID:
        bot.send_message(message.chat.id, 'Да, хозяин')


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            sleep(5)
