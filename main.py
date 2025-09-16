# -*- coding: utf-8 -*-

from codecs import decode
import time #Модуль подключаемый с библиотекой shedull
import threading #Модуль многопоточности, для отправки расписания по времени
import schedule #Модуль для запуска функций по заданному расписанию
import telebot #Модуль работы с библиотеками телеграмма
from telebot import types
from telebot.types import InputFile
from telebot.types import ReplyKeyboardRemove
from datetime import datetime #Модуль для работы с временем
from raspisanie import get_raspisanie



bot = telebot.TeleBot("7274101025:AAH7AwcHJrJo25rLYrAAyziGtALBq1JkQvs")

data_file = 'users.txt'  # Файл для хранения данных пользователей

# Функция для загрузки данных пользователей
def load_users():
    users = {}
    try:
        with open(data_file, 'r') as file:
            for line in file:
                user_id, role, notifications = line.strip().split(',')
                users[int(user_id)] = {'role': role, 'notifications': notifications == 'True'}
    except FileNotFoundError: #ПОДУМАЙТЕ ПОЖАЛУЙСТА Я НЕ ХОЧУ!!!
        text = "Сервер временно недоступен" 
        bot.send_message(user_id, text)
        pass
    return users

# Функция для сохранения данных пользователей
def save_users():
    with open(data_file, 'w') as file:
        for user_id, data in users.items():
            file.write(f"{user_id},{data['role']},{data['notifications']}\n")

# Инициализация пользователей
users = load_users()
events = []

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Добро пожаловать! я ваш Личный ассистент! Выберите вашу роль:", reply_markup=role_keyboard())

def role_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Студент"), types.KeyboardButton("Преподаватель"))
    return keyboard

@bot.message_handler(func=lambda message: message.text in ['Студент', 'Преподаватель'])
def handle_role_selection(message):
    role = message.text
    if role in ['Студент', 'Преподаватель']:
        users[message.chat.id] = {'role': role, 'notifications': True}
        save_users()  # Сохраняем данные
        bot.send_message(message.chat.id, f"Вы выбрали {role}. Напишите /help для доступных команд.")
        bot.send_message(message.chat.id, "Клавиатура удалена", reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите корректную роль.")
        
@bot.message_handler(commands=['help'])
def help_message(message):
    commands = "/schedule - Получить расписание\n/events - Посмотреть мероприятия"
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("/schedule"), types.KeyboardButton("/events"))

    if users[message.chat.id]["role"] == "Преподаватель":
        commands += "\n/schedule_change - Изменить расписание"
        commands += "\n/events_change - Изменить мероприятия"
        keyboard.add(types.KeyboardButton("/schedule_change"))
        keyboard.add(types.KeyboardButton("/events_change"))

    bot.send_message(message.chat.id, commands, reply_markup=keyboard)

@bot.message_handler(commands=['schedule'])
def shedule_message(message):
    commands = "~Расписание!~"
    bot.send_message(message.chat.id, commands)
    send_schedule()

@bot.message_handler(commands=['schedule_change'])
def shedule_message(message):
    commands = "Вот расписание\nОтправте изменённое расписание"
    bot.send_message(message.chat.id, commands)
    file = open('files/lesson_schedule.xlsx', 'rb')
    bot.send_document(message.chat.id, file)

@bot.message_handler(content_types=["document"])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    from openpyxl import load_workbook
    from io import BytesIO
    wb = load_workbook(filename=BytesIO(downloaded_file))
    wb.save("files/lesson_schedule.xlsx")

    bot.reply_to(message, 'Я пожалуй сохраню это')

def send_schedule():
    for user_id in users.keys():
        text = get_raspisanie(datetime.now().weekday() + 1)
        text = "\n".join(["-".join(x) for x in text])
        bot.send_message(user_id, text)
        pass

events_data = {
    "event1": {
        'image_url': 'https://sun9-13.userapi.com/impg/aWvZmbWBg6eLWtPODZIaH_2oEsK84VI5NFJIDg/IckZIMsHyvs.jpg?size=807x509&quality=95&sign=ffefd03f828b8580e8f30bc9bd308089&type=album',
        'caption': 'Описание первого мема: Привет, я рот ебал ваш тг бот. Время 6:52. Я уже выплакал все что было. Все работает криво',
        'name': 'Название мероприятия 1'
    },
    "event2": {
        'image_file': 'images.jpg',
        'caption': 'Описание второго мема: Привет, я рот ебал ваш тг бот. Время 5:27. Я хочу плакать. Как сделать описание? :)',
        'name': 'Название мероприятия 2'
    },
}

@bot.message_handler(commands=['events'])        
def send_event_photos(message):
    user_id = message.chat.id
    for event_id, event_name in events_data.items():
        if 'image_url' in event_name:
            bot.send_photo(user_id, event_name['image_url'], caption=event_name['caption'])
            show_registration_status(message, event_id, event_name)
        elif 'image_file' in event_name:
            with open(event_name['image_file'], 'rb') as photo:
                bot.send_photo(user_id, photo, caption=event_name['caption'])
                show_registration_status(message, event_id, event_name)
        

def show_registration_status(message, event_id, event_name):
    user_id = message.chat.id
    if 'registered_events' not in users.get(user_id, {}):
        users[user_id]['registered_events'] = {}
    
    registered = users[user_id]['registered_events'].get(event_id, False)
    button_text = f"Регистрация: {'Да ✔' if registered else 'Нет ❌'}"
    callback_data = "unregister" if registered else "register"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=button_text, callback_data=f"{callback_data}:{event_id}"))
    bot.send_message(user_id, event_name['name'], reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('register', 'unregister')))
def handle_registration(call):
    user_id = call.message.chat.id
    action, event_id = call.data.split(':')

    if 'registered_events' not in users.get(user_id, {}):
        users[user_id]['registered_events'] = {}
        
    if action == 'register':
        users[user_id]['registered_events'][event_id] = True
        bot.send_message(user_id, f"Вы успешнозарегистрированы на {events_data[event_id]['name']}.")
    else:
        users[user_id]['registered_events'][event_id] = False
        bot.send_message(user_id, f"Вы отменили регистрацию на {events_data[event_id]['name']}.")

    save_users()
    show_registration_status(call.message, event_id, events_data[event_id])

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.chat.id not in users:
        bot.send_message(message.chat.id, "Не могу распознать вашу команду. Пожалуйста, выберите роль на клавиатуре.")
        return
    if users[message.chat.id]["role"] == "Преподаватель":
        bot.send_message(message.chat.id, f"УважаемыйНе могу распознать вашу команду, возможно, разрабы ее еще не доделали)."\
                                            "\n Напишите /help для доступных команд.")
    elif users[message.chat.id]["role"] == "Студент":
        bot.send_message(message.chat.id, f"Не могу распознать вашу команду, возможно, разрабы ее еще не доделали)."\
                                            "\n Напишите /help для доступных команд.")
    else:
        bot.send_message(message.chat.id, f"Не могу распознать вашу команду. Пожалуйста, перезапустите бота написав /start).")

schedule.every().day.at("08:00").do(send_schedule) #ставим нужное время. В это время будет отправлять всем расписание

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    bot.polling(none_stop=True)