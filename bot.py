import os
import sqlite3
from tkinter import Image
import telebot
from telebot import types
from datetime import datetime, timedelta
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import jdatetime
import time
# Initialize bot
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Connect to SQLite database
conn = sqlite3.connect('group_management.db', check_same_thread=False)
cursor = conn.cursor()

# Ensure the Members table has the total_payments column
def add_total_payments_column():
    try:
        cursor.execute('ALTER TABLE Members ADD COLUMN total_payments INTEGER DEFAULT 0')
        conn.commit()
    except sqlite3.OperationalError:
        # The column may already exist
        pass
# افزودن ستون description به جدول Expenses اگر وجود ندارد
def add_description_column():
    try:
        cursor.execute('ALTER TABLE Expenses ADD COLUMN description TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # اگر ستون از قبل وجود داشته باشد، ارور نادیده گرفته می‌شود
        pass

def add_pet_joined_date_column():
    try:
        cursor.execute('ALTER TABLE Pets ADD COLUMN pet_joined_date TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # اگر ستون از قبل وجود داشته باشد، ارور نادیده گرفته می‌شود
        pass

# افزودن ستون توضیحات به جدول Expenses
add_description_column()
# Add the column if it's not already present
add_total_payments_column()

add_pet_joined_date_column()

# Create tables if they do not exist

# ایجاد جدول‌ها
cursor.execute('''
CREATE TABLE IF NOT EXISTS Members (
    member_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,  -- تضمین یکتا بودن username
    first_name TEXT,
    joined_date TEXT,
    last_payment_date TEXT,
    total_payments INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount INTEGER,
    payment_date TEXT,
    FOREIGN KEY(member_id) REFERENCES Members(member_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER,
    description TEXT,
    expense_date TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS FutureExpenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER NOT NULL,
    expense_date TEXT NOT NULL,
    description TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Pets (
    pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_name TEXT,
    pet_type TEXT,
    pet_age FLOAT,
    pet_breed TEXT,
    pet_description TEXT,
    pet_cost INTEGER,
    pet_photo TEXT,
    pet_joined_date TEXT
)
''')

conn.commit()

AUTHORIZED_USERS = [
    {'username': 'NemokiaZ', 'id': None},
    {'username':'Sylviekia', 'id': None},
    {'username': 'Hasti_moslemi', 'id': None},
]

def is_user_authorized(member_id: int, username: str) -> bool:
    for user in AUTHORIZED_USERS:
        if user['id'] == member_id or user['username'] == username:
            return True
    return False

'''@bot.message_handler(content_types=['text'])
def get_chat_id(message):
    if message.chat.type in ['group', 'supergroup']:
        group_id = message.chat.id
        bot.send_message(message.chat.id, f"شناسه گروه: {group_id}")
        return'''


@bot.message_handler(commands=['start'])
def show_main_menu(message):
    """Main menu"""
    if message.chat.type in ['group', 'supergroup']:
        bot.send_message(message.from_user.id, 'لطفا درخواست خود را در ربات بگویید.')
        return
    user_id = message.from_user.id
    username = message.from_user.username

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_user_authorized(user_id, username):
        markup.add('مدیریت هزینه ها')

    markup.add('دریافت گزارشات پرداخت')
    markup.add('فرشته ها')

    bot.send_message(message.chat.id, 'به ربات خوش آمدید! لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'مدیریت هزینه ها')
def payments_menu(message):
    """Menu for adding payments."""
    if message.chat.type in ['group', 'supergroup']:
        # ارسال پیام به صورت خصوصی
        bot.send_message(message.from_user.id, 'لطفا درخواست خود را در ربات بگویید')
        return
    
    if is_user_authorized(message.from_user.id, message.from_user.username):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('💰 ثبت پرداختی ها')
        markup.add('💸 اضافه کردن هزینه پیش رو')
        markup.add('حذف هزینه پیش رو')
        markup.add('بازگشت')  # دکمه بازگشت به منوی اصلی
        
        bot.send_message(message.chat.id, 'منو مدیریت هزینه ها', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "شما دسترسی ندارید.")

@bot.message_handler(func=lambda message: message.text == 'دریافت گزارشات پرداخت')
def reports_menu(message):
    if message.chat.type in ['group', 'supergroup']:
    # ارسال پیام به صورت خصوصی
        bot.send_message(message.from_user.id, 'لطفا درخواست خود را در ربات بگویید')
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📊 دریافت گزارش گروه', "📔 دریافت گزارش شخصی")
    markup.add('دریافت هزینه های پیش رو')
    markup.add('بازگشت')  # دکمه بازگشت به منوی اصلی

    bot.send_message(message.chat.id,'گزارش ها', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'فرشته ها')
def show_pets_menu(message, pet_id=None, pet=None):
    # بررسی اینکه آیا پیام در گروه است
    if message.chat.type in ['group', 'supergroup']:
        # ارسال پیام به صورت خصوصی
        bot.send_message(message.from_user.id, 'لطفا درخواست خود را در ربات بگویید')
        return

    # اگر پیام در گروه نبود
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_user_authorized(message.from_user.id, message.from_user.username):
        markup.add("❌ حذف حیوان", "➕ افزودن حیوان")
        markup.add("✏️ ویرایش حیوان")
        
    markup.add("🐕 مشاهده حیوانات")
    markup.add('بازگشت')  # دکمه بازگشت به منوی اصلی

    bot.send_message(message.from_user.id, 'منوی فرشته ها', reply_markup=markup)  # ارسال پیام به کاربر
    
@bot.message_handler(func=lambda message: message.text == 'لیست فرشته ها')
def list_of_pets_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('همه فرشته ها')
    markup.add('بر اساس گونه و نژاد')
    markup.add('بازگشت به منو قبلی')  # دکمه بازگشت به منوی اصلی

    bot.send_message(message.chat.id, 'منوی لیست فرشته ها', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    """
    Handle a menu button click.
    """
    user_id = message.from_user.id
    username = message.from_user.username

    if message.text == "📔 دریافت گزارش شخصی":
        send_personal_report(message)

    elif message.text == '📊 دریافت گزارش گروه':
        group_report_handler(message)
        
    elif message.text == 'دریافت هزینه های پیش رو':
        view_future_expenses_handler(message)

    elif message.text == '💸 اضافه کردن هزینه پیش رو':
        if is_user_authorized(user_id, username):
            add_future_expense_handler(message)
        else:
            bot.send_message(message.chat.id, "شما دسترسی ندارید.")

    elif message.text == 'حذف هزینه پیش رو':
        if is_user_authorized(user_id, username):
            delete_future_expense_handler(message)
        else:
            bot.send_message(message.chat.id, "شما دسترسی ندارید.")

    elif message.text == '💰 ثبت پرداختی ها':
        if is_user_authorized(user_id, username):
            add_expense(message)
        else:
            bot.send_message(message.chat.id, "شما دسترسی ندارید.")

    elif message.text == "➕ افزودن حیوان":
        if is_user_authorized(user_id, username):
            get_pet_id(message)
        else:
            bot.send_message(message.chat.id, "شما دسترسی ندارید.")

    elif message.text =="✏️ ویرایش حیوان":
        if is_user_authorized(user_id, username):
            edit_pet(message)
        else:
            bot.send_message(message.chat.id, "شما دسترسی ندارید.")

    elif message.text == "🐕 مشاهده حیوانات":
        list_of_pets_menu(message)
    
    elif message.text == "همه فرشته ها":
        list_of_pets(message)

    elif message.text == 'بر اساس گونه و نژاد':
        choose_filter_option(message)

    elif message.text == "❌ حذف حیوان":
        if is_user_authorized(user_id, username):
            remove_pet(message)
        else:
            bot.send_message(message.chat.id, "شما دسترسی ندارید.")

    elif message.text == 'بازگشت':
        show_main_menu(message)
    elif message.text == 'بازگشت به منو قبلی':
        show_pets_menu(message)

    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های منو را انتخاب کنید.")


# Send welcome message to new members
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    for new_member in message.new_chat_members:
        cursor.execute('INSERT INTO Members (member_id, username, first_name, joined_date, last_payment_date) VALUES (?, ?, ?, ?, ?)', 
                       (new_member.id, new_member.username, new_member.first_name, datetime.now().strftime('%Y-%m-%d'), None))
        conn.commit()
        # پیام خوش‌آمدگویی و منوی اولیه
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('دریافت گزارشات پرداخت', 'مدیریت هزینه ها', 'فرشته ها')
        bot.send_message(message.chat.id, f"خوش آمدید @{new_member.username or new_member.id}!", reply_markup=markup)
@bot.message_handler(func=lambda message: True)
def auto_start_for_old_users(message):
    member_id = message.from_user.id
    cursor.execute('SELECT * FROM Members WHERE member_id = ?', (member_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('INSERT INTO Members (member_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)', 
                       (member_id, message.from_user.username, message.from_user.first_name, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('دریافت گزارشات پرداخت', 'مدیریت هزینه ها', 'فرشته ها')
        bot.send_message(message.chat.id, 'به ربات خوش آمدید! لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:', reply_markup=markup)

# Remind members for payment if they haven't paid in the last month (by the start of each month)
def remind_for_payment():
    cursor.execute('SELECT member_id, username, last_payment_date FROM Members')
    members = cursor.fetchall()
    current_date = datetime.now()
    
    for member in members:
        member_id, username, last_payment_date = member
        if not is_user_authorized(member_id, username):
            if last_payment_date:
                last_payment_date = datetime.strptime(last_payment_date, '%Y-%m-%d')
                months_since_last_payment = (current_date.year - last_payment_date.year) * 12 + (current_date.month - last_payment_date.month)

                if months_since_last_payment >= 2:
                    # ارسال پیام به کاربر
                    bot.send_message(member_id, f"⛔️ @{username}، شما 2 ماه متوالی پرداخت نداشتید. لطفاً مبلغ پرداختی خود را به‌روز کنید.")
                    
                    # ارسال پیام به ادمین‌ها
                    for admin in AUTHORIZED_USERS:
                        if admin['id']:
                            bot.send_message_by_username(admin['username'], f"⚠️ کاربر @{username} ({member_id}) 2 ماه متوالی پرداخت نداشته است.")
                elif months_since_last_payment == 1:
                    bot.send_message(member_id, f"یادآوری: شما در ماه گذشته پرداختی نداشته‌اید. لطفاً مبلغ پرداختی خود را به‌روز کنید.")
            else:
                # اگر کاربر هنوز پرداختی نداشته باشد
                bot.send_message(member_id, "یادآوری: شما هنوز پرداختی نداشته‌اید.")


# Detect members leaving the group
@bot.message_handler(content_types=['left_chat_member'])
def handle_left_member(message):
    left_member = message.left_chat_member
    cursor.execute('DELETE FROM Members WHERE member_id = ?', (left_member.id,))
    conn.commit()
    bot.send_message(message.chat.id, f"{left_member.first_name} has left the group and will no longer be tracked for payments.")

@bot.message_handler(func= lambda message: True)
def handle_message(message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        return
    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های منو را انتخاب کنید.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        sender_id = message.from_user.id

        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton('بله', callback_data='confirm_payment')
        cancel_btn = types.InlineKeyboardButton('خیر', callback_data='cancel_payment')
        markup.add(confirm_btn, cancel_btn)
        bot.send_message(sender_id, "آیا عکسی که فرستادید برای اهدای مبلغ به گروه می باشد",reply_markup=markup )
# Handle cancel payment button
@bot.callback_query_handler(func=lambda call: call.data == 'cancel_payment')
def cancel_payment(call, message=None):
    # Handle callback query to cancel payment
    if call:
        try:
            # Edit the message to remove reply markup
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            # Notify the user that the payment has been canceled
            bot.send_message(call.message.chat.id, "پرداخت لغو شد.")  # "Payment canceled."
        except Exception as e:
            print(f"Error in cancel_payment (call): {e}")
    elif message:
        try:
            # Notify the user that the payment has been canceled
            bot.send_message(message.chat.id, "پرداخت لغو شد.")  # "Payment canceled."
        except Exception as e:
            print(f"Error in cancel_payment (message): {e}")
    
    # Return to the main menu after cancellation
    show_main_menu(call.message.chat.id)  # Ensure you're passing the correct chat ID


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_payment')
def confirm_payment(call):
    member_id = call.from_user.id
    username = call.from_user.username

    cursor.execute('UPDATE Members SET last_payment_date = ? WHERE member_id = ?', (datetime.now().strftime('%Y-%m-%d'), member_id))
    conn.commit()    
    # حذف دکمه‌ها پس از تأیید
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    # ارسال پیام جدید برای درخواست مبلغ پرداختی
    msg = bot.send_message(call.message.chat.id, "چقدر به تومان پرداخت کرده‌اید؟\nاگر اشتباه انتخاب کردید عدد 0 بگزارید")
    
    # استفاده از لامبدا برای انتقال member_id
    bot.register_next_step_handler(msg, lambda m: payment_amount(m, member_id))

def payment_amount(message, member_id):
    try:
        amount = int(message.text)
        if amount == 0:
            cancel_payment(call=None, message=message)
        elif amount > 1000:
            cursor.execute('INSERT INTO Payments (member_id, amount, payment_date) VALUES (?, ?, ?)', 
                           (member_id, amount, datetime.now().strftime('%Y-%m-%d')))
            cursor.execute('UPDATE Members SET total_payments = total_payments + ? WHERE member_id = ?', 
                           (amount, member_id))
            conn.commit()
            
            # ارسال پیام تشکر
            bot.send_message(message.chat.id, "✅ پرداخت شما با موفقیت ثبت شد!\n🙏 از پرداخت شما سپاسگزاریم!")
            # بازگشت به منوی اصلی پس از موفقیت پرداخت
            show_main_menu(message)
        else:
            bot.send_message(message.chat.id, "مبلغ وارد شده نمی‌تواند کمتر از 1000 تومان باشد. لطفاً مبلغ صحیح را وارد کنید:")
            bot.register_next_step_handler(message, lambda m: payment_amount(m, member_id))
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً یک عدد معتبر وارد کنید:")
        bot.register_next_step_handler(message, lambda m: payment_amount(m, member_id))

@bot.message_handler(commands=['group_report'])
def group_report_handler(message):
    """اضافه کردن دکمه‌های اینلاین برای انتخاب نوع گزارش گروه."""
    markup = types.InlineKeyboardMarkup()
    detailed_report_button = types.InlineKeyboardButton("ریز هزینه‌های یک ماه گذشته", callback_data='view_last_month_expenses')
    summary_report_button = types.InlineKeyboardButton("گزارش کلی هزینه‌ها", callback_data='view_summary_expenses')
    markup.add(detailed_report_button, summary_report_button)
    
    bot.send_message(message.chat.id, "لطفاً نوع گزارشی که می‌خواهید را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['view_last_month_expenses', 'view_summary_expenses'])
def handle_group_report_selection(call):
    """نمایش گزارش بر اساس انتخاب و حذف دکمه‌های اینلاین."""
    # حذف دکمه‌های اینلاین
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    if call.data == 'view_last_month_expenses':
        # نمایش ریز هزینه‌های یک ماه گذشته
        one_month_ago = (jdatetime.date.today() - timedelta(days=30)).strftime('%Y-%m-%d')  # تاریخ به شمسی
        cursor.execute('SELECT amount, expense_date, description FROM Expenses WHERE expense_date >= ?', (one_month_ago,))
        expenses = cursor.fetchall()
        #print(one_month_ago)
        
        if expenses:
            report = "📋 **ریز هزینه‌های یک ماه گذشته**:\n\n"
            for amount, expense_date, description in expenses:
                report += f"💸 مبلغ: {amount:,} تومان\n📅 تاریخ: {expense_date}\n📝 توضیحات: {description}\n\n"

            bot.send_message(call.message.chat.id, report)
        else:
            bot.send_message(call.message.chat.id, "هیچ هزینه‌ای در یک ماه گذشته ثبت نشده است.")
    
    elif call.data == 'view_summary_expenses':
        # نمایش گزارش کلی هزینه‌ها
        send_group_report(call.message)

def send_group_report(message):
    """ایجاد و ارسال گزارش کلی گروه"""

    # مجموع پرداخت‌های ماه گذشته
    one_month_ago = datetime.now() - timedelta(days=30)
    cursor.execute('SELECT SUM(amount) FROM Payments WHERE payment_date >= ?', (one_month_ago.strftime('%Y-%m-%d'),))
    monthly_payments = cursor.fetchone()[0] or 0

    # مجموع پرداخت‌های هفته گذشته
    one_week_ago = datetime.now() - timedelta(days=7)
    cursor.execute('SELECT SUM(amount) FROM Payments WHERE payment_date >= ?', (one_week_ago.strftime('%Y-%m-%d'),))
    weekly_payments = cursor.fetchone()[0] or 0

    # مجموع تمام پرداختی‌ها از ابتدا
    cursor.execute('SELECT SUM(amount) FROM Payments')
    total_payments = cursor.fetchone()[0] or 0

    # مجموع هزینه‌های صورت گرفته
    cursor.execute('SELECT SUM(amount) FROM Expenses')
    total_expenses = cursor.fetchone()[0] or 0

    # مجموع باقی‌مانده در حساب گروه
    remaining_balance = total_payments - total_expenses

    # ایجاد گزارش
    report = (
        f"📊 **گزارش کلی هزینه‌های گروه**:\n\n"
        f"💰 مجموع پرداخت‌های ماه گذشته: {monthly_payments:,} تومان\n"
        f"💰 مجموع پرداخت‌های هفته گذشته: {weekly_payments:,} تومان\n"
        f"💰 مجموع تمام پرداختی‌ها از ابتدا: {total_payments:,} تومان\n"
        f"💸 مجموع هزینه‌ها: {total_expenses:,} تومان\n"
        f"💼 موجودی باقی‌مانده: {remaining_balance:,} تومان"
    )

    # ارسال گزارش به گروه
    bot.send_message(message.chat.id, report)

def send_personal_report(message):
    member = message.chat.id
    #print(member)
    user = message.chat.username
    #print(user)

    # تاریخ امروز و محاسبه تاریخ‌های ماه و هفته گذشته
    today = datetime.now()
    first_day_of_current_month = today.replace(day=1)
    first_day_of_last_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
    first_day_of_last_week = today - timedelta(days=today.weekday())
    first_day_of_week = first_day_of_last_week - timedelta(days=7)

    # محاسبه مجموع پرداخت‌ها
    cursor.execute('''
        SELECT SUM(amount) FROM Payments
        WHERE member_id = ? AND payment_date >= ?
    ''', (member, first_day_of_last_month.strftime('%Y-%m-%d')))
    monthly_payments = cursor.fetchone()[0] or 0

    cursor.execute('''
        SELECT SUM(amount) FROM Payments
        WHERE member_id = ? AND payment_date >= ?
    ''', (member, first_day_of_week.strftime('%Y-%m-%d')))
    weekly_payments = cursor.fetchone()[0] or 0

    cursor.execute('''
        SELECT SUM(amount) FROM Payments
        WHERE member_id = ?
    ''', (member,))
    total_payments = cursor.fetchone()[0] or 0

    # ساخت پیام
    report_message = (
        f"📊 **گزارش مالی شخصی{user}**:\n\n"
        f"💰 مجموع پرداخت‌های ماه گذشته: {monthly_payments:,} تومان\n"
        f"💰 مجموع پرداخت‌های هفته گذشته: {weekly_payments:,} تومان\n"
        f"💰 مجموع تمام پرداختی‌ها از ابتدا: {total_payments:,} تومان"
    )

    # ارسال پیام
    #bot.send_message(message.chat.id, report_message)
    bot.reply_to(message, report_message)
@bot.message_handler(commands=['add_expense'])
def add_expense(message):
    """Handle add expense command."""
    user_id = message.from_user.id
    username = message.from_user.username

    if is_user_authorized(user_id, username):
        msg = bot.send_message(message.chat.id, "لطفاً مبلغ خرج شده را وارد کنید:")
        bot.register_next_step_handler(msg, get_amount)
    else:
        bot.send_message(message.chat.id, "⛔️ شما اجازه‌ی اضافه کردن هزینه را ندارید.")

def get_amount(message):
    """Get amount from user and validate it."""
    try:
        amount = int(message.text)
        if amount <= 0:
            bot.send_message(message.chat.id, "⛔️ مبلغ وارد شده نامعتبر است. لطفاً یک عدد معتبر وارد کنید.")
            return
        msg = bot.send_message(message.chat.id, "لطفاً توضیحات هزینه را وارد کنید:")
        bot.register_next_step_handler(msg, lambda m: save_expense(m, amount))
    except ValueError:
        bot.send_message(message.chat.id, "⛔️ لطفاً یک عدد معتبر وارد کنید.")

def save_expense(message, amount):
    """Save expense to database."""
    description = message.text
    cursor.execute('INSERT INTO Expenses (amount, expense_date, description) VALUES (?, ?, ?)', 
                   (amount, datetime.now().strftime('%Y-%m-%d'), description))
    conn.commit()
    
    bot.send_message(message.chat.id, f"✅ هزینه {amount} تومان با موفقیت ثبت شد!\n📋 توضیحات: {description}")

    # بازگشت به منوی payments_menu
    payments_menu(message)


@bot.message_handler(commands=['future_expense'])
def add_future_expense_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username
    if is_user_authorized(user_id, username):
        msg = bot.send_message(message.chat.id, "لطفاً مبلغ هزینه پیش رو را وارد کنید:")
        bot.register_next_step_handler(msg, process_future_expense_amount)
    else:
        bot.send_message(message.chat.id, "⛔️ شما اجازه‌ی اضافه کردن هزینه پیش رو را ندارید.")
def process_future_expense_amount(message):
    try:
        amount = int(message.text)
        bot.send_message(message.chat.id, "برای لغو پرداخت عدد صفر را وارد کنید")
        if amount == 0:
            cancel_payment(call=None, message=message)
            show_main_menu(message)
        elif amount <= 0:
            bot.send_message(message.chat.id, "⛔️ مبلغ وارد شده نامعتبر است. لطفاً یک عدد معتبر وارد کنید.")
            return
        msg = bot.send_message(message.chat.id, "لطفاً توضیحات مربوط به این هزینه پیش رو را وارد کنید:")
        bot.register_next_step_handler(msg, lambda m: save_future_expense(m, amount))
    except ValueError:
        bot.send_message(message.chat.id, "⛔️ لطفاً یک عدد معتبر وارد کنید.")
        return
def save_future_expense(message, amount):
    description = message.text
    expense_date = jdatetime.date.today().strftime('%Y-%m-%d')  # تاریخ به شمسی
    
    cursor.execute('INSERT INTO FutureExpenses (amount, expense_date, description) VALUES (?, ?, ?)', 
                   (amount, expense_date, description))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ هزینه پیش رو به مبلغ {amount:,} تومان با موفقیت ثبت شد!\n📋 توضیحات: {description}")
    payments_menu(message)

@bot.message_handler(commands=['view_future_expenses'])
def view_future_expenses_handler(message):
    """نمایش تمام هزینه‌های پیش رو تا زمانی که حذف نشوند."""
    cursor.execute('SELECT amount, expense_date, description FROM FutureExpenses')
    future_expenses = cursor.fetchall()
    
    if future_expenses:
        report = "📋 **گزارش هزینه‌های پیش رو**:\n\n"
        for amount, expense_date, description in future_expenses:
            report += f"💸 مبلغ: {amount:,} تومان\n📅 تاریخ: {expense_date}\n📝 توضیحات: {description}\n\n"
        bot.send_message(message.chat.id, report)
    else:
        bot.send_message(message.chat.id, "هیچ هزینه‌ای ثبت نشده است.")


@bot.message_handler(commands=['delete_future_expense'])
def delete_future_expense_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username
    if is_user_authorized(user_id, username):  # بررسی مجوز ادمین
        msg = bot.send_message(message.chat.id, "لطفاً قسمتی از توضیحات هزینه‌ای که می‌خواهید حذف کنید را وارد کنید:")
        bot.register_next_step_handler(msg, process_delete_future_expense)
    else:
        bot.send_message(message.chat.id, "⛔️ شما اجازه‌ی حذف هزینه پیش رو را ندارید.")

def process_delete_future_expense(message):
    description_part = message.text  # دریافت قسمت توضیحات
    cursor.execute('SELECT * FROM FutureExpenses WHERE description LIKE ?', ('%' + description_part + '%',))
    expenses = cursor.fetchall()
    
    if expenses:
        response = "✅ هزینه‌های زیر با توضیحات مشابه پیدا شدند:\n"
        for expense in expenses:
            response += f"ID: {expense[0]},\nمبلغ💸 {expense[1]},\nتاریخ📅: {expense[2]},\nتوضیحات📝:{expense[3]}\n\n"
        
        response += "\nلطفاً ID هزینه‌ای که می‌خواهید حذف کنید را وارد کنید:"
        bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(message, confirm_delete_expense)
    else:
        bot.send_message(message.chat.id, "⛔️ هیچ هزینه‌ای با این توضیحات یافت نشد.")

def confirm_delete_expense(message):
    expense_id = message.text  # دریافت ID هزینه
    cursor.execute('DELETE FROM FutureExpenses WHERE id = ?', (expense_id,))
    conn.commit()
    
    if cursor.rowcount > 0:
        bot.send_message(message.chat.id, f"✅ هزینه با ID {expense_id} با موفقیت حذف شد!")
        payments_menu(message)
    else:
        bot.send_message(message.chat.id, "⛔️ هیچ هزینه‌ای با این ID یافت نشد.")

@bot.message_handler(commands=['add_pet'])
def get_pet_id(message):
    random_id = random.randint(100000, 999999)
    while pet_id_exists(random_id):
        random_id = random.randint(100000, 999999)

    bot.send_message(message.chat.id, f"شناسه حیوان  شما: {random_id}")
    msg = bot.send_message(message.chat.id, "لطفاً نام حیوان  را وارد کنید:", reply_markup=cancel_button())
    bot.register_next_step_handler(msg, lambda m: get_pet_name(m, random_id))

def pet_id_exists(pet_id):
    cursor.execute('SELECT pet_id FROM Pets WHERE pet_id = ?', (pet_id,))
    result = cursor.fetchone()
    return result is not None

def cancel_button():
    """Creates a cancel button for use in each step."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('❌ لغو')
    return markup

def get_pet_name(message, pet_id):
    if message.text == '❌ لغو':
        cancel_addition(message)
        return
    pet_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "لطفاً گونه حیوان  را وارد کنید:", reply_markup=cancel_button())
    bot.register_next_step_handler(msg, lambda m: get_pet_type(m, pet_id, pet_name))

def get_pet_type(message, pet_id, pet_name):
    if message.text == '❌ لغو':
        cancel_addition(message)
        return
    pet_type = message.text.strip()
    msg = bot.send_message(message.chat.id, "لطفاً سن حیوان  را وارد کنید:", reply_markup=cancel_button())
    bot.register_next_step_handler(msg, lambda m: get_pet_age(m, pet_id, pet_name, pet_type))

def get_pet_age(message, pet_id, pet_name, pet_type):
    if message.text == '❌ لغو':
        cancel_addition(message)
        return
    try:
        pet_age = float(message.text)
        msg = bot.send_message(message.chat.id, "لطفاً نژاد حیوان  را وارد کنید:", reply_markup=cancel_button())
        bot.register_next_step_handler(msg, lambda m: get_pet_breed(m, pet_id, pet_name, pet_type, pet_age))
    except ValueError:
        bot.send_message(message.chat.id, "⛔ سن باید عددی معتبر باشد. لطفاً دوباره امتحان کنید.")
        bot.register_next_step_handler(message, lambda m: get_pet_age(m, pet_id, pet_name, pet_type))

def get_pet_breed(message, pet_id, pet_name, pet_type, pet_age):
    if message.text == '❌ لغو':
        cancel_addition(message)
        return
    pet_breed = message.text.strip()
    msg = bot.send_message(message.chat.id, "لطفاً توضیحات اضافی را وارد کنید (اختیاری):", reply_markup=cancel_button())
    bot.register_next_step_handler(msg, lambda m: get_pet_description(m, pet_id, pet_name, pet_type, pet_age, pet_breed))

def get_pet_description(message, pet_id, pet_name, pet_type, pet_age, pet_breed):
    if message.text == '❌ لغو':
        cancel_addition(message)
        return
    pet_description = message.text.strip()
    msg = bot.send_message(message.chat.id, "لطفاً هزینه اولیه را وارد کنید (به تومان):", reply_markup=cancel_button())
    bot.register_next_step_handler(msg, lambda m: get_pet_cost(m, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description))

def get_pet_cost(message, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description):
    if message.text == '❌ لغو':
        cancel_addition(message)
        return
    try:
        pet_cost = int(message.text)
        msg = bot.send_message(message.chat.id, "اگر مایلید، یک عکس از حیوان  خود ارسال کنید (اختیاری). اگر نمی‌خواهید، 'خیر' را تایپ کنید:", reply_markup=cancel_button())
        bot.register_next_step_handler(msg, lambda m: get_pet_photo(m, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost))
    except ValueError:
        bot.send_message(message.chat.id, "⛔ هزینه باید عددی معتبر باشد. لطفاً دوباره امتحان کنید.")
        bot.register_next_step_handler(message, lambda m: get_pet_cost(m, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description))


def get_unique_file_name(pet_id, pet_name):
    return f"{pet_id}_{pet_name}.jpg"
def validate_photo_size(file_info: telebot.types.File, max_size_mb: int = 5) -> None:
    """Validate that a photo is within a certain size limit."""
    file_size_kb = file_info.file_size / 1024
    if file_size_kb > max_size_mb * 1024:
        raise ValueError(f"File size exceeds {max_size_mb} MB ({file_size_kb:.2f} KB)")

def get_pet_photo(message, pet_id: int, pet_name: str, pet_type: str, pet_age: int, pet_breed: str, pet_description: str, pet_cost: int) -> None:
    """Get a pet photo from the user and save the pet."""
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        try:
            validate_photo_size(file_info)
        except ValueError as e:
            bot.send_message(message.chat.id, str(e))
            return

        downloaded_file = bot.download_file(file_info.file_path)
        photo_dir = "photos"
        os.makedirs(photo_dir, exist_ok=True)
        pet_photo_path = os.path.join(photo_dir, get_unique_file_name(pet_id, pet_name))
        with open(pet_photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        save_pet(message, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, pet_photo_path)

    elif message.text.strip().lower() == 'خیر':
        save_pet(message, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, None)

    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('خیر')
        bot.send_message(message.chat.id, "لطفاً یک عکس ارسال کنید یا 'خیر' را تایپ کنید:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda m: get_pet_photo(m, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost))

# Cancel the pet addition process
def cancel_addition(message):
    bot.send_message(message.chat.id, "❌ فرایند اضافه کردن حیوان  لغو شد.", reply_markup=types.ReplyKeyboardRemove())
    show_main_menu(message)


def save_pet(message, pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, pet_photo):
    # دریافت تاریخ امروز به شمسی
    today = jdatetime.date.today()
    pet_joined_date = today.strftime("%Y/%m/%d")  # تاریخ به فرمت YYYY/MM/DD

    # ذخیره اطلاعات حیوان  در دیتابیس
    cursor.execute(''' 
        INSERT INTO Pets (pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, pet_photo, pet_joined_date) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) 
    ''', (pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, pet_photo, pet_joined_date))
    conn.commit()

    # ایجاد گزارش ثبت حیوان  جدید
    report = (
        f"✅ حیوان  جدید با موفقیت ثبت شد!\n\n"
        f"📋 **مشخصات حیوان **:\n"
        f"🔹 ID: {pet_id}\n"
        f"🔹 نام: {pet_name}\n"
        f"🔹 نوع: {pet_type}\n"
        f"🔹 سن: {pet_age} سال\n"
        f"🔹 نژاد: {pet_breed}\n"
        f"🔹 توضیحات: {pet_description or 'ندارد'}\n"
        f"🔹 هزینه: {pet_cost:,} تومان\n"
        f"🔹 تاریخ ثبت: {pet_joined_date}"
    )

    # ارسال گزارش حیوان  جدید به کاربر
    if pet_photo and os.path.exists(pet_photo):  # اگر عکس موجود باشد، آن را ارسال می‌کنیم
        with open(pet_photo, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=report, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, report, parse_mode='Markdown')

    # بازگشت به منوی اصلی بعد از نمایش اطلاعات
    show_main_menu(message)


@bot.message_handler(commands=['list_of_pets'])
def list_of_pets(message):
    cursor.execute('SELECT pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, pet_photo, pet_joined_date FROM Pets')
    pets = cursor.fetchall()

    if pets:
        for pet in pets:
            pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost, pet_photo, pet_joined_date = pet

            # بررسی None بودن مقادیر و جایگزینی با یک متن پیش‌فرض
            pet_name = pet_name if pet_name else "نامشخص"
            pet_type = pet_type if pet_type else "نامشخص"
            pet_age = pet_age if pet_age else "نامشخص"
            pet_breed = pet_breed if pet_breed else "نامشخص"
            pet_description = pet_description if pet_description else "توضیحی موجود نیست"
            pet_cost = pet_cost if pet_cost else 0  # اگر هزینه None بود، 0 نمایش می‌دهد

            report = (f"ID: {pet_id}\n"
                      f"**نام**: {pet_name}\n"
                      f"**نوع**: {pet_type}\n"
                      f"**سن**: {pet_age} سال\n"
                      f"**نژاد**: {pet_breed}\n"
                      f"**توضیحات**: {pet_description}\n"
                      f"**هزینه**: {pet_cost:,} تومان\n"
                      f"**تاریخ ثبت**: {pet_joined_date}\n"  # نمایش تاریخ ثبت
                      f"<<<<<<>>>>>\n")

            # ارسال عکس در صورت وجود
            if pet_photo and os.path.exists(pet_photo):  # بررسی وجود فایل
                with open(pet_photo, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=report, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, report + "عکسی موجود نیست.")
    else:
        bot.send_message(message.chat.id, "هیچ حیوان  در سیستم ثبت نشده است.")


@bot.message_handler(commands=['remove_pet'])
def remove_pet(message):
    """Remove a pet."""
    msg = bot.send_message(message.chat.id, "لطفاً شناسه یا نام حیوان  که می‌خواهید حذف کنید را وارد کنید:")
    bot.register_next_step_handler(msg, process_remove_pet_input)

def process_remove_pet_input(message):
    pet_input = message.text.strip()

    try:
        pet_id = int(pet_input)
        cursor.execute('SELECT pet_id, pet_name, pet_type, pet_breed, pet_photo FROM Pets WHERE pet_id = ?', (pet_id,))
        pet = cursor.fetchone()
        if pet:
            confirm_removal(message, pet[0], pet[1], pet[2], pet[3], pet[4])  # اضافه کردن مسیر تصویر
        else:
            bot.send_message(message.chat.id, "❌ حیوان  با این شناسه پیدا نشد.")
    except ValueError:
        pet_name = pet_input
        cursor.execute('SELECT pet_id, pet_name, pet_type, pet_breed, pet_photo FROM Pets WHERE pet_name LIKE ?', (f'%{pet_name}%',))
        pets = cursor.fetchall()

        if len(pets) == 0:
            bot.send_message(message.chat.id, "❌ حیوان  با این نام یا شناسه پیدا نشد.")
        elif len(pets) > 1:
            report = "📋 لیست حیوانات  با نام مشابه:\n\n"
            for pet in pets:
                report += f"ID: {pet[0]}\nنام: {pet[1]}\nگونه: {pet[2]}\nنژاد: {pet[3]}\n\n"
            bot.send_message(message.chat.id, report, parse_mode='Markdown')

            msg = bot.send_message(message.chat.id, "لطفاً شناسه حیوان  مورد نظر برای حذف را وارد کنید:")
            bot.register_next_step_handler(msg, process_remove_pet_input)
        else:
            pet = pets[0]
            confirm_removal(message, pet[0], pet[1], pet[2], pet[3], pet[4])

def confirm_removal(message, pet_id, pet_name, pet_type, pet_breed, pet_photo):
    """تایید نهایی برای حذف حیوان به همراه نمایش گونه و نژاد."""
    markup = telebot.types.InlineKeyboardMarkup()
    yes_button = telebot.types.InlineKeyboardButton("بله", callback_data=f"confirm_remove:{pet_id}")
    no_button = telebot.types.InlineKeyboardButton("خیر", callback_data="cancel_remove")
    markup.add(yes_button, no_button)

    bot.send_message(message.chat.id, 
                     f"آیا مطمئنید که می‌خواهید حیوان  '{pet_name}' با شناسه {pet_id}، گونه '{pet_type}' و نژاد '{pet_breed}' را حذف کنید؟",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_remove'))
def remove_confirmed_pet(call):
    """حذف نهایی حیوان بعد از تایید."""
    pet_id = int(call.data.split(':')[1])

    # گرفتن اطلاعات حیوان  از پایگاه داده
    cursor.execute('SELECT pet_name, pet_type, pet_photo FROM Pets WHERE pet_id = ?', (pet_id,))
    pet_info = cursor.fetchone()

    # حذف دکمه‌های اینلاین پس از کلیک
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    if pet_info:
        pet_name = pet_info[0]
        pet_type = pet_info[1]
        image_path = pet_info[2]

        try:
            cursor.execute('DELETE FROM Pets WHERE pet_id = ?', (pet_id,))
            conn.commit()

            # حذف تصویر از سیستم فایل
            if image_path and os.path.exists(image_path):
                os.remove(image_path)

            # ارسال پیام موفقیت‌آمیز
            bot.send_message(call.message.chat.id, f"✅ حیوان  {pet_name} از گونه {pet_type} با شناسه {pet_id} با موفقیت حذف شد.")
        except sqlite3.Error as e:
            bot.send_message(call.message.chat.id, f"خطایی رخ داد: {e}")
    else:
        bot.send_message(call.message.chat.id, "❌ حیوان  با این شناسه پیدا نشد.")


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_remove')
def cancel_removal(call):
    """لغو عملیات حذف."""
    # حذف دکمه‌های اینلاین
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    bot.send_message(call.message.chat.id, "❌ حذف حیوان  لغو شد.")
    show_main_menu(call.message)  # بازگشت به منوی اصلی


def process_pet_removal(message):
    pet_input = message.text

    try:
        # بررسی اینکه آیا ورودی یک عدد است (ID حیوان )
        pet_id = int(pet_input)
        cursor.execute('DELETE FROM Pets WHERE pet_id = ?', (pet_id,))
    except ValueError:
        # اگر ورودی عدد نبود، فرض می‌شود که نام حیوان است
        pet_name = pet_input
        cursor.execute('DELETE FROM Pets WHERE pet_name = ?', (pet_name,))

    conn.commit()

    if cursor.rowcount > 0:
        bot.reply_to(message, "✅ حیوان  با موفقیت حذف شد!")
        show_main_menu(message)
    else:
        bot.reply_to(message, "❌ حیوان  با این ID یا نام پیدا نشد.")


def show_back_button(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn_back = types.KeyboardButton('بازگشت')
    markup.add(btn_back)
    bot.send_message(message.chat.id, "برای بازگشت دکمه زیر را فشار دهید:", reply_markup=markup)


def edit_pet(message):
    msg = bot.send_message(
        message.chat.id, "لطفاً شناسه یا نام حیوان  که می‌خواهید ویرایش کنید را وارد کنید:")
    bot.register_next_step_handler(msg, process_pet_input)

def process_pet_input(message):
    pet_input = message.text.strip()

    # بررسی اینکه آیا ورودی یک عدد است (ID حیوان )
    try:
        pet_id = int(pet_input)
        pet = get_pet_info(pet_id)  # دریافت اطلاعات حیوان بر اساس ID
        if pet:
            show_edit_menu(message, pet_id, pet)
        else:
            bot.send_message(message.chat.id, "❌ حیوان  با این ID پیدا نشد.")
    except ValueError:
        # اگر ورودی عدد نبود، فرض می‌شود که نام حیوان است
        pet_name = pet_input
        cursor.execute('SELECT pet_id, pet_name, pet_type, pet_age, pet_breed FROM Pets WHERE pet_name LIKE ?', (f'%{pet_name}%',))
        pets = cursor.fetchall()

        if len(pets) == 0:
            bot.send_message(message.chat.id, "❌ حیوان  با این نام پیدا نشد.")
        elif len(pets) == 1:
            pet_id = pets[0][0]
            pet = get_pet_info(pet_id)
            show_edit_menu(message, pet_id, pet)
        else:
            # اگر چند حیوان با نام مشابه پیدا شد، لیست آن‌ها را نمایش بده
            report = "📋 **لیست حیوانات  با نام مشابه**:\n\n"
            for pet in pets:
                pet_id, pet_name, pet_type, pet_age, pet_breed = pet
                report += (f"ID: {pet_id}\n"
                           f"نام: {pet_name}\n"
                           f"نوع: {pet_type}\n"
                           f"سن: {pet_age} سال\n"
                           f"نژاد: {pet_breed}\n\n")
            bot.send_message(message.chat.id, report, parse_mode='Markdown')

            # درخواست شناسه از کاربر برای انتخاب حیوان
            msg = bot.send_message(message.chat.id, "لطفاً شناسه حیوان  مورد نظر برای ویرایش را وارد کنید:")
            bot.register_next_step_handler(msg, process_pet_id)

def process_pet_id(message):
    """دریافت شناسه حیوان از کاربر و نمایش منوی ویرایش."""
    try:
        pet_id = int(message.text.strip())
        pet = get_pet_info(pet_id)
        if pet:
            show_edit_menu(message, pet_id, pet)
        else:
            bot.send_message(message.chat.id, "❌ حیوان  با این ID پیدا نشد.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ شناسه معتبر نیست. لطفاً دوباره تلاش کنید.")

def show_edit_menu(message, pet_id, pet):
    """نمایش منوی ویرایش."""
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('ویرایش نام', 'ویرایش نوع', 'ویرایش سن', 'ویرایش نژاد', 'ویرایش توضیحات', 'ویرایش هزینه', 'ویرایش عکس')
    markup.add('بازگشت')
    bot.send_message(message.chat.id, "لطفاً یکی از موارد زیر را برای ویرایش انتخاب کنید:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: handle_edit_selection(m, pet_id, pet))

def handle_edit_selection(message, pet_id, pet):
    options = {
        'ویرایش نام': edit_pet_name,
        'ویرایش نوع': edit_pet_type,
        'ویرایش سن': edit_pet_age,
        'ویرایش نژاد': edit_pet_breed,
        'ویرایش توضیحات': edit_pet_description,
        'ویرایش هزینه': edit_pet_cost,
        'ویرایش عکس': edit_pet_photo,
        'بازگشت': show_pets_menu
    }
    options[message.text.strip()](message, pet_id, pet)

def get_pet_info(pet_id):
    """دریافت اطلاعات حیوان  با شناسه داده شده."""
    cursor.execute('SELECT pet_id, pet_name, pet_type, pet_age, pet_breed, pet_description, pet_cost FROM Pets WHERE pet_id = ?', (pet_id,))
    return cursor.fetchone()

def back_to_edit_menu(message, pet_id, pet):
    """بازگشت به منوی ویرایش."""
    show_edit_menu(message, pet_id, pet)

def create_back_to_edit_menu():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('بازگشت به منوی ویرایش')
    return markup

def edit_pet_name(message, pet_id, pet):
    pet_name = pet[1]
    markup = create_back_to_edit_menu()
    msg = bot.send_message(
        message.chat.id, 
        f"نام فعلی: {pet_name}\nلطفاً نام جدید را وارد کنید یا بازگشت را انتخاب کنید:", 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, lambda m: process_new_name(m, pet_id ,pet))

def process_new_name(message, pet_id, pet):
    if message.text == 'بازگشت به منوی ویرایش':
        back_to_edit_menu(message, pet_id, pet)
    else:
        new_name = message.text.strip()
        
        if not new_name:
            bot.send_message(message.chat.id, "❌ نام نمی‌تواند خالی باشد. لطفاً نام جدید را وارد کنید.")
            edit_pet_name(message, pet_id, get_pet_info(pet_id))  # Re-prompt for the name
            return

        try:
            cursor.execute('UPDATE Pets SET pet_name = ? WHERE pet_id = ?', (new_name, pet_id))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ نام حیوان  با موفقیت به {new_name} تغییر یافت.")
            updated_pet = get_pet_info(pet_id)
            back_to_edit_menu(message, pet_id, updated_pet)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطا در تغییر نام: {str(e)}")
            edit_pet_name(message, pet_id, get_pet_info(pet_id))  # Prompt again in case of failure

def edit_pet_type(message, pet_id, pet):
    pet_type = pet[2]
    markup = create_back_to_edit_menu()
    msg = bot.send_message(message.chat.id, f"نوع فعلی: {pet_type}\nلطفاً نوع جدید را وارد کنید:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_new_type(m, pet_id, pet))

def process_new_type(message, pet_id, pet):
    if message.text == 'بازگشت به منوی ویرایش':
        back_to_edit_menu(message, pet_id, pet)
    else:
        new_type = message.text.strip()
        # بررسی خالی بودن ورودی
        if not new_type:
            bot.send_message(message.chat.id, "❌ لطفاً یک نوع معتبر وارد کنید.")
            edit_pet_type(message, pet_id, pet)  # بازگشت به ویرایش نوع
            return
        
        try:
            cursor.execute('UPDATE Pets SET pet_type = ? WHERE pet_id = ?', (new_type, pet_id))
            conn.commit()

            bot.send_message(message.chat.id, f"✅ گونه حیوان  شما با موفقیت به {new_type} تغییر یافت.")        
            # بارگذاری اطلاعات جدید
            updated_pet = get_pet_info(pet_id)
            back_to_edit_menu(message, pet_id, updated_pet)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطا در به روزرسانی نوع حیوان: {str(e)}")
            edit_pet_age(message, pet_id, [None, None, new_type])

def edit_pet_age(message, pet_id, pet):
    pet_age = pet[3]
    markup = create_back_to_edit_menu()
    msg = bot.send_message(message.chat.id, f"سن فعلی: {pet_age} سال 🐾\nلطفاً سن جدید را وارد کنید:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_new_age(m, pet_id, pet))

def process_new_age(message, pet_id, pet):
    if message.text == 'بازگشت به منوی ویرایش':
        back_to_edit_menu(message, pet_id, pet)
    else:
        try:
            new_age = float(message.text.strip())
            if new_age < 0:
                raise ValueError
            cursor.execute('UPDATE Pets SET pet_age = ? WHERE pet_id = ?', (new_age, pet_id))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ سن حیوان  با موفقیت به {new_age} سال تغییر یافت.")
            updated_pet = get_pet_info(pet_id)
            back_to_edit_menu(message, pet_id, updated_pet)
        except ValueError:
            bot.reply_to(message, "❌ سن باید یک عدد مثبت باشد. لطفاً دوباره وارد کنید.")
            edit_pet_age(message, pet_id, [None, None, None, new_age])

# ویرایش نژاد حیوان
def edit_pet_breed(message, pet_id, pet):
    pet_breed = pet[4]
    markup = create_back_to_edit_menu()
    msg = bot.send_message(
        message.chat.id,
        f"🐶 نژاد فعلی: {pet_breed}\nلطفاً نژاد جدید را وارد کنید:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, lambda m: process_new_breed(m, pet_id, pet))
def process_new_breed(message, pet_id, pet):
    if message.text == 'بازگشت به منوی ویرایش':
        back_to_edit_menu(message, pet_id, pet)
    else:
        new_breed = message.text.strip()
        if new_breed:
            cursor.execute('UPDATE Pets SET pet_breed = ? WHERE pet_id = ?', (new_breed, pet_id))
            conn.commit()
            bot.send_message(message.chat.id, f"✅ نژاد حیوان  با موفقیت به {new_breed} تغییر یافت.")
            updated_pet = get_pet_info(pet_id)
            back_to_edit_menu(message, pet_id, updated_pet)
        else:
            bot.reply_to(message, "❌ نژاد نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید.")
            edit_pet_breed(message, pet_id,pet)

def edit_pet_description(message, pet_id, pet):
    pet_description = pet[5]  # Directly get the pet description
    markup = create_back_to_edit_menu()
    msg = bot.send_message(
        message.chat.id, 
        f"🐾 توضیحات فعلی: {pet_description}\n📝 لطفاً توضیحات جدید را وارد کنید:", 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, lambda m: process_new_description(m, pet_id, pet))
def process_new_description(message, pet_id, pet):
    if message.text == 'بازگشت به منوی ویرایش':
        back_to_edit_menu(message, pet_id,pet)
    else:
        new_description = message.text.strip()
        cursor.execute('UPDATE Pets SET pet_description = ? WHERE pet_id = ?', (new_description, pet_id))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ توضیحات حیوان  با موفقیت به: \"{new_description}\" تغییر یافت.")
        back_to_edit_menu(message, pet_id, pet)

# ویرایش هزینه حیوان 🐾
def edit_pet_cost(message, pet_id, pet):
    pet_cost = pet[6]  # Assuming pet_cost is at index 6
    markup = create_back_to_edit_menu()  # Create back button
    msg = bot.send_message(message.chat.id, f"💰 هزینه فعلی: {pet_cost}\nلطفاً هزینه جدید را وارد کنید:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_new_cost(m, pet_id, pet))

def process_new_cost(message, pet_id, pet):
    if message.text == 'بازگشت به منوی ویرایش':
        back_to_edit_menu(message, pet_id, pet)  # Back to edit menu 🔄
    else:
        try:
            # Check for empty input first
            if message.text.strip() == "":
                raise ValueError("ورود خالی!")

            new_cost = float(message.text.strip())
            if new_cost < 0:
                raise ValueError("هزینه منفی!")
            new_cost = message.text.strip()
            cursor.execute('UPDATE Pets SET pet_cost = ? WHERE pet_id = ?', (new_cost, pet_id))
            conn.commit()  # Save changes in database
            bot.send_message(message.chat.id, f"✅ هزینه حیوان  با موفقیت به {new_cost} تغییر یافت.")
            back_to_edit_menu(message, pet_id, pet)  # Back to edit menu 🔄
        
        except ValueError as e:
            bot.reply_to(message, f"❌ خطا: {e}. لطفاً دوباره عددی مثبت وارد کنید:")

@bot.callback_query_handler(func=lambda call: call.data == 'show_pets_menu')
def show_pets_menu_on_cancel(call):
    """Return to the pets menu after canceling an operation."""
    bot.answer_callback_query(call.id)  # Respond to the button click
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="عملیات لغو شد.")

    show_pets_menu(call.message)

def edit_pet_photo(message, pet_id, pet):
    """
    Edit a pet's photo by sending a new one.
    """
    pet_photo = pet[7] if len(pet) > 7 and pet[7] is not None else "عکسی موجود نیست"
    
    markup = create_back_to_edit_menu()

    if not pet_photo:
        prompt = "❌ عکسی ذخیره نشده است. لطفاً عکس جدید را ارسال کنید:"
    else:
        prompt = f"📸 عکس فعلی: {pet_photo}\nلطفاً عکس جدید را ارسال کنید:"

    msg = bot.send_message(message.chat.id, prompt, reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: handle_pet_photo_edit(m, pet_id, pet))

    cancel_btn = types.InlineKeyboardButton("کنسل", callback_data='show_pets_menu')
    markup = types.InlineKeyboardMarkup().add(cancel_btn)
    bot.edit_message_reply_markup(message.chat.id, msg.message_id, reply_markup=markup)

def handle_pet_photo_edit(message, pet_id, pet):
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        photo_dir = "photos"
        os.makedirs(photo_dir, exist_ok=True)
        photo_path = os.path.join(photo_dir, f"{pet_id}_{pet[1]}.jpg")

        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        cursor.execute('UPDATE Pets SET pet_photo = ? WHERE pet_id = ?', (photo_path, pet_id))
        conn.commit()

        bot.send_message(message.chat.id, "✅ عکس حیوان  با موفقیت به‌روزرسانی شد.")
    else:
        bot.send_message(message.chat.id, "بدون تغییر در عکس.")
    
    back_to_edit_menu(message, pet_id, pet)

def get_edited_pet_info(pet_id):
    cursor.execute('SELECT * FROM Pets WHERE pet_id = ?', (pet_id,))
    row = cursor.fetchone()
    if row:
        return {
            'pet_id': row[0],
            'pet_name': row[1],
            'pet_type': row[2],
            'pet_age': row[3],
            'pet_breed': row[4],
            'pet_description': row[5],  # توضیحات
            'pet_cost': row[6],          # هزینه
            'pet_photo': row[7]
        }
    return None

@bot.message_handler(commands=['list_pets'])
def choose_filter_option(message):
    """نمایش گزینه‌های فیلتر کردن حیوانات بر اساس گونه یا نژاد."""
    markup = types.InlineKeyboardMarkup()
    type_button = types.InlineKeyboardButton("بر اساس گونه", callback_data='view_by_type')
    markup.add(type_button)
    
    bot.send_message(message.chat.id, "لطفاً یک گونه را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'view_by_type')
def choose_species(call):
    """نمایش لیست گونه‌ها برای انتخاب."""
    # حذف دکمه‌های اینلاین پس از کلیک
    
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    # دریافت تمام گونه‌ها از دیتابیس
    cursor.execute('SELECT DISTINCT pet_type FROM Pets')
    species = cursor.fetchall()
    if species:
        markup = types.InlineKeyboardMarkup()
        for species_tuple in species:
            markup.add(types.InlineKeyboardButton(species_tuple[0], callback_data=f"select_species:{species_tuple[0]}"))
        bot.send_message(call.message.chat.id, "لطفاً گونه‌ای را انتخاب کنید:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "هیچ گونه‌ای در سیستم موجود نیست.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_species'))
def choose_breed(call):
    """نمایش نژادهای ثبت شده برای گونه انتخابی."""
    # حذف دکمه‌های اینلاین پس از کلیک
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    species = call.data.split(':')[1]  # استخراج گونه انتخاب شده
    # دریافت نژادهای مرتبط با گونه انتخاب شده از دیتابیس
    cursor.execute('SELECT DISTINCT pet_breed FROM Pets WHERE pet_type = ?', (species,))
    breeds = cursor.fetchall()
    
    if breeds:
        markup = types.InlineKeyboardMarkup()
        for breed_tuple in breeds:
            markup.add(types.InlineKeyboardButton(breed_tuple[0], callback_data=f"select_breed:{breed_tuple[0]}"))
        bot.send_message(call.message.chat.id, f"لطفاً یک نژاد از گونه {species} را انتخاب کنید:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, f"هیچ نژادی برای گونه {species} یافت نشد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_breed'))
def show_pets_by_breed(call):
    """نمایش حیوانات ثبت شده بر اساس نژاد انتخابی."""
    # حذف دکمه‌های اینلاین پس از کلیک
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    breed = call.data.split(':')[1]  # استخراج نژاد انتخاب شده
    # دریافت حیوانات مرتبط با نژاد انتخاب شده از دیتابیس
    cursor.execute('SELECT pet_name, pet_type, pet_age, pet_breed, pet_cost FROM Pets WHERE pet_breed = ?', (breed,))
    pets = cursor.fetchall()
    
    if pets:
        report = f"🐾 **حیوانات ثبت شده در نژاد ({breed})**:\n\n"
        for pet in pets:
            report += f"نام: {pet[0]}\nگونه: {pet[1]}\nسن: {pet[2]} سال\nهزینه: {pet[4]:,} تومان\n\n"
        bot.send_message(call.message.chat.id, report)
    else:
        bot.send_message(call.message.chat.id, f"هیچ حیوانی در نژاد {breed} یافت نشد.")


# Polling
while True: 
    try:
        bot.infinity_polling(timeout=10 , long_polling_timeout=5)
    except Exception as e:
        print(f'خطا رخ داده: {e}')
        time.sleep(5)
