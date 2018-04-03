import json
from telebot import types


class Games:
    def __init__(self):
        jsObj = open("jsonout.json", "r", encoding="UTF-8")

        self.introduction, self.roles, self.clues, self.game_result = json.load(jsObj)

        jsObj.close()

        self.players = dict()  # словарь игроков ключ - id, значение - объект игрока
        self.game_flag = False  # флаг игры, пока игра не начата в состоянии False

        self.chat_id = None  # id часта

        self.times = 10  # время для того, чтобы собраться игрокам

        self.night_time = 60  # время для ночи
        self.day_time = 30  # время для обсуждения
        self.vote_time = 30  # время для голосования

    # статус игры возвращает False, пока игра не закончится
    def game_status(self, bot):
        for player in self.players.values():
            if player.role['killer'] == 'Yes' and player.blame_digits >= len(self.players) // 2 + 1:
                bot.send_message(self.chat_id, self.game_result['win'])
        else:
            bot.send_message(self.chat_id, self.game_result['fail'])

    # генерация ролей
    def gen_role(self):
        players_list = list(self.players.keys())
        for i in players_list:
            self.players[i].role = self.roles.pop()


class Gamer:
    def __init__(self, username, gamer_id, chat_id, true_username):
        self.blame_digits = 0
        self.username = username  # Имя и фамилия пользователя
        self.gamer_id = gamer_id
        self.chat_id = chat_id
        self.true_username = true_username  # username пользователя, если есть
        self.slowpoke_flag = True  # Флаг несовершения действия
        self.role = None
        self.message_id = 0

    def about_role(self, bot):
        bot.send_message(self.gamer_id, self.role['discription'])

    def clues_search(self, bot, clue, n_clue):
        keyboard = types.InlineKeyboardMarkup(1)
        for j, i in enumerate(clue['actions']):
            button = types.InlineKeyboardButton(callback_data='check_' + str(n_clue) + "_" + str(j),
                                                text=i['button_text'])
            keyboard.add(button)
        text_message = bot.send_message(self.gamer_id, 'Что из этого исследуешь?', reply_markup=keyboard)
        self.message_id = text_message.message_id

    def voting(self, bot, game):
        keyboard = types.InlineKeyboardMarkup(1)
        for j in game.players.values():
            if j.gamer_id != self.gamer_id:
                button = types.InlineKeyboardButton(callback_data='kill_' + str(j.gamer_id), text=j.role['name'])
                keyboard.add(button)
        text_message = bot.send_message(self.gamer_id, 'Как думаешь кто убийца?', reply_markup=keyboard)
        self.message_id = text_message.message_id

    def send_slowpoke(self, bot):
        if self.slowpoke_flag:
            try:
                bot.edit_message_text(chat_id=self.gamer_id, message_id=self.message_id, text='Время вышло!')
            except:
                bot.send_message(chat_id=self.gamer_id, text='Кто-то слишком долго думает')

        self.slowpoke_flag = True
