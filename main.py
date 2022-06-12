import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import requests
import re
import time

# Сетим токен
API_TOKEN = ''

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    new = State()

# Прием /start
@dp.message_handler(commands='start', state='*')
async def start_cmd_handler(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup()

    keyboard_markup.add(types.InlineKeyboardButton(text='Рассчитать новый хэшрейт', callback_data='new'))

    await message.reply("Привет! Тут можно проверить доход майнига эфира", reply_markup=keyboard_markup)


# Ответ на кнопку для нового хр
@dp.callback_query_handler(text='new', state='*')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await Form.new.set()
    await query.answer()
    await query.message.answer('Введите ваш хэшрейт, MH/s')

# Ответ на кнопку введенного хр
@dp.callback_query_handler(text='old', state='*')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(is_old=True)
    await query.answer()
    await new_handler(query.message, state)

# Запрос в апи
@dp.message_handler(state=Form.new)
async def new_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    if 'user_hash' in data and data['is_old'] is True:
        userHashrate = data['user_hash']
    else:
        userHashrate = message.text
    print(userHashrate)
    if userHashrate.replace('.', '', 1).isdigit() or userHashrate.replace(',', '', 1).isdigit():
        correctUserHashrate = float(userHashrate.replace(',', '.'))
        print(correctUserHashrate)
        link_url = "https://2cryptocalc.com/ajax/ru/algo/now/ethash/" + str(correctUserHashrate)
        response = requests.get(link_url)
        print(link_url)

        # Переменные с доходом
        Eth_Day = re.findall(
            r'"profit":{"html":"<span class=\\"crypto-val text-right\\"><span class=\\"crypto-val__text\\"><span class=\\"text-val\\">(.*?)<',
            response.text)[0]
        print(Eth_Day)
        Eth_Hour = round((float(Eth_Day) / 24), 2)
        Eth_Week = round((float(Eth_Day) * 7), 2)
        Eth_Month = round((float(Eth_Day) * 30), 2)
        Eth_Year = round((float(Eth_Day) * 365), 2)
        print('Значения получены')
        if 'is_old' not in data or 'is_old' in data and data['is_old'] is True:
            await state.update_data(is_old=False)
        if 'is_old' not in data or 'is_old' in data and data['is_old'] is False:
            await state.update_data(user_hash=message.text)

        # Добавляем клавиатуру в ответ
        keyboard_markup = types.InlineKeyboardMarkup()

        keyboard_markup.add(types.InlineKeyboardButton(text='Рассчитать новый хэшрейт', callback_data='new'))
        keyboard_markup.add(types.InlineKeyboardButton(text='Перерасчитать для введенного', callback_data='old'))

        await message.answer(
            f'<b>Хэшрейт:</b> {correctUserHashrate} MH/s\n\n<b><u>Доход:</u></b>\n<b>В час:</b> {Eth_Hour} $\n<b>В день:</b> {Eth_Day} $\n<b>В неделю:</b> {Eth_Week} $\n<b>В месяц:</b> {Eth_Month} $\n<b>В год:</b> {Eth_Year} $',
            parse_mode="HTML",reply_markup=keyboard_markup)
    else:
        # Обрабатываем невалидности
        await bot.send_message(message.chat.id, 'Ошибка! Введите корректное значение!')

#Перезапуск
if __name__ == '__main__':
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            time.sleep(2)
            print(e)
