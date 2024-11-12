import telebot
from telebot import types
from datetime import datetime, timedelta
import threading
import schedule
import time

# Inisialisasi bot dengan token
API_TOKEN = '7588785950:AAFfEZzqnb6fUC1zHLwCXKmk_a0kOdg-Ylg'
bot = telebot.TeleBot(API_TOKEN)

# Data pengguna disimpan dalam format dictionary
user_data = {}

# Fungsi menyapa pengguna baru
@bot.message_handler(commands=['start'])
def welcome(message):
    hour = datetime.now().hour
    greeting = "Selamat pagi" if 5 <= hour < 12 else "Selamat siang" if 12 <= hour < 18 else "Selamat malam"
    bot.reply_to(message, f"{greeting}, {message.from_user.first_name}! Saya adalah bot pengingat tugas Anda. Ketik /menu untuk melihat opsi yang tersedia.")

# Menampilkan menu utama
@bot.message_handler(commands=['menu'])
def main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Tambah Tugas')
    btn2 = types.KeyboardButton('Lihat Tugas')
    btn3 = types.KeyboardButton('Bantuan')
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Pilih opsi:", reply_markup=markup)

# Menambahkan tugas dengan konfirmasi
@bot.message_handler(func=lambda message: message.text == "Tambah Tugas")
def add_task(message):
    bot.send_message(message.chat.id, "Silakan masukkan deskripsi tugas Anda.")
    bot.register_next_step_handler(message, get_task_description)

def get_task_description(message):
    user_data[message.from_user.id] = {"description": message.text}
    bot.send_message(message.chat.id, "Silakan masukkan deadline dalam format YYYY-MM-DD HH:MM")
    bot.register_next_step_handler(message, get_task_deadline)

def get_task_deadline(message):
    try:
        deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        user_data[message.from_user.id]["deadline"] = deadline
        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton("Konfirmasi", callback_data="confirm_task")
        cancel_btn = types.InlineKeyboardButton("Batal", callback_data="cancel_task")
        markup.add(confirm_btn, cancel_btn)
        bot.send_message(message.chat.id, f"Tugas Anda: {user_data[message.from_user.id]['description']}\nDeadline: {deadline}", reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Format tanggal dan waktu tidak valid. Silakan coba lagi.")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_task", "cancel_task"])
def handle_task_confirmation(call):
    if call.data == "confirm_task":
        bot.answer_callback_query(call.id, "Tugas Anda telah disimpan.")
    elif call.data == "cancel_task":
        bot.answer_callback_query(call.id, "Tugas dibatalkan.")
        bot.send_message(call.message.chat.id, "Silakan tambahkan tugas baru dengan perintah /menu.")

# Menampilkan daftar tugas
@bot.message_handler(func=lambda message: message.text == "Lihat Tugas")
def view_tasks(message):
    tasks = user_data.get(message.from_user.id)
    if tasks and "deadline" in tasks:
        response = f"Berikut adalah tugas Anda:\n\nDeskripsi: {tasks['description']}\nDeadline: {tasks['deadline']}\n"
    else:
        response = "Anda belum memiliki tugas."
    bot.send_message(message.chat.id, response)

# Menambahkan bantuan dengan emoji
@bot.message_handler(func=lambda message: message.text == "Bantuan")
def send_help(message):
    bot.send_message(
        message.chat.id,
        "📚 Berikut adalah perintah yang tersedia:\n"
        "/menu - Menampilkan menu utama\n"
        "/help - Bantuan\n"
        "Gunakan menu untuk menambah atau melihat tugas!"
    )

# Mengirim pengingat otomatis H-1 sebelum deadline
def send_task_reminder():
    now = datetime.now()
    for user_id, task in user_data.items():
        if "deadline" in task:
            time_diff = task["deadline"] - now
            if timedelta(hours=23) <= time_diff < timedelta(days=1):  # H-1
                bot.send_message(user_id, f"Pengingat: Tugas '{task['description']}' akan segera jatuh tempo besok!")

# Menjalankan pengingat di thread terpisah
def run_scheduler():
    schedule.every().day.at("09:00").do(send_task_reminder)
    while True:
        schedule.run_pending()
        time.sleep(1)

reminder_thread = threading.Thread(target=run_scheduler)
reminder_thread.start()

# Menjalankan bot
bot.polling()