#!/usr/bin/python3.6
# -- coding: utf-8 --
import json
import telebot
from telebot import types
import time
import config
import core
import random

jsObj = open("jsonout.json", "r", encoding="UTF-8")

introduction, roles, clues, game_result = json.load(jsObj)

jsObj.close()

bot = telebot.TeleBot(config.token)

game = core.Games()


# главная функция
@bot.message_handler(commands=['startgame'])
def start_game(message):
    global game

    if not game.game_flag:  # если игра еще не запущена
        game.game_flag = True

        # создается клавиатура с кнопкой с ссылкой на бота
        # добавление в игру осуществляется функцией add_users
        game.chat_id = message.chat.id
        keyboard = types.InlineKeyboardMarkup()
        callback_button = types.InlineKeyboardButton(url='telegram.me/sherloki_bot?start={0}'.format(game.chat_id),
                                                     text='join')
        keyboard.add(callback_button)

        step = 10  # интервал обновления таймера в секундах
        times_format = '{0:0>2}:{1:0>2}'.format(game.times // 60, game.times % 60)
        players_format = '\n'.join([j.username for j in game.players.values()])  # строка со списком всех игроков

        # считываение имени и фамилии пользователя
        name = []
        if message.from_user.first_name:
            name.append(message.from_user.first_name)
        if message.from_user.last_name:
            name.append(message.from_user.last_name)
        name = ' '.join(name)

        # клавиатура посылается в чат
        text = ("<a href='http://telegram.me/{0}'>{4}</a> начал игру\nКоличество игроков: {1}\n"
                "Осталось времени: {2}\n{3}".format(message.from_user.username, len(game.players),
                                                    times_format, players_format, name))
        send = bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode="HTML",
                                disable_web_page_preview=True)

        # изменять значение таймера, пока не выйдет время
        while game.times > 0:
            game.times -= step
            time.sleep(step)
            times_format = '{0:0>2}:{1:0>2}'.format(game.times // 60, game.times % 60)
            players_format = ('\n'.join(["<a href='http://telegram.me/{0}'>{1}</a>".format(j.true_username, j.username)
                                         for j in game.players.values()]))
            text = ("<a href='http://telegram.me/{0}'>{4}</a> начал игру\nКоличество игроков: {1}\n"
                    "Осталось времени: {2}\n{3}".format(message.from_user.username, len(game.players),
                                                        times_format, players_format, name))

            bot.edit_message_text(chat_id=message.chat.id, message_id=send.message_id, text=text, reply_markup=keyboard,
                                  parse_mode="HTML", disable_web_page_preview=True)

        # удаление клавиатуры с кнопкой
        bot.edit_message_text(chat_id=game.chat_id, message_id=send.message_id, text=text, parse_mode="HTML",
                              disable_web_page_preview=True)

        if len(game.players) < 1:
            bot.send_message(message.chat.id, 'Эх, мало игроков(((')
            game = core.Games()

        else:
            bot.send_message(message.chat.id, 'Ура, собрались!\nТак, сейчас раздам всем роли\n')
            bot.send_message(message.chat.id, game.introduction)
            game.gen_role()  # генерация ролей

            # отправление информации о роли
            for player in game.players.values():
                player.about_role(bot)

            for n_clue, clue in enumerate(game.clues):

                # стадия алиби
                bot.send_message(message.chat.id, "Стадия алиби")

                time.sleep(30)
                bot.send_message(message.chat.id, "Стадия улик")
                # дневные действия

                for player in game.players.values():
                    times = 30
                    player.clues_search(bot, clue, n_clue)
                    while times and player.slowpoke_flag == True:
                        time.sleep(1)
                        times -= 1
                    player.send_slowpoke(bot)
            for player in game.players.values():
                player.voting(bot, game)

            times = 30

            while times >= 0 and not all(map(lambda x: x.slowpoke_flag == False, game.players.values())):
                times -= 1
                time.sleep(1)

            game.game_status(bot)

            game = core.Games()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global game
    if game.game_flag:
        data = call.data.split('_')
        if data[0] == "kill":
            game.players[int(data[1])].blame_digits += 1
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Выбор принят ' + game.players[int(data[1])].role['name'])
            game.players[call.message.chat.id].slowpoke_flag = False
        elif data[0] == 'check':
            out_text = game.clues[int(data[1])]['actions'].pop(int(data[2]))['text']
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=out_text)
            bot.send_message(game.chat_id, out_text)
            game.players[call.message.chat.id].slowpoke_flag = False


@bot.message_handler(commands=['start'])
def add_users(message):
    global game
    text = message.text.split()
    if len(text) > 1:  # проверка на то, что человек нажал start, а не прислал команду
        if game.game_flag:  # проверка на то, что начата игра

            # считываение имени и фамилии пользователя
            name = []
            if message.from_user.first_name:
                name.append(message.from_user.first_name)
            if message.from_user.last_name:
                name.append(message.from_user.last_name)
            name = ' '.join(name)

            game.players[message.from_user.id] = core.Gamer(name, message.from_user.id, int(text[1]),
                                                            message.from_user.username)  # создание объекта игрока

            bot.send_message(message.from_user.id, 'Ты присоединился!')


@bot.message_handler(commands=['forcestart'])
def force_start():
    global game
    if game.game_flag:
        game.times = 0


if __name__ == '__main__':
    bot.polling(none_stop=True)
