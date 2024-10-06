
Telegram Group & Pets Management Bot

This is a Python-based Telegram bot designed to manage group members and their payments, as well as pets information. The bot uses Telebot and SQLite for its operations. Key features include:

User payments tracking: Add payments, view group reports, and remind users about payments.

Expenses management: Add and view future expenses for the group.

Pets management: Add, edit, view, and delete pet information including their photos.

Authorization system: Only authorized users can manage payments and pets.


Table of Contents

1. Features


2. Prerequisites


3. Installation


4. Configuration


5. Running the Bot


6. Database Schema


7. Error Handling and Polling


8. Contributing


9. License



Features <a name="features"></a>

Group and Payments Management:

Track user payments and generate individual or group reports.

Send reminders to users who haven’t made payments in the past month.

View and add future expenses.

Authorized users can manage the group expenses.


Pets Management:

Add, view, edit, and delete pet information (including photos).

Restrict pet management features to authorized users only.


Authorization System:

Only specific users (with usernames or IDs) can manage pets or payments.

View-only access for non-authorized users.


Prerequisites <a name="prerequisites"></a>

Before you begin, ensure you have met the following requirements:

Python 3.7+

A Telegram bot token (you can get this from BotFather).

SQLite for local database management.

telebot Python library (install with pip install pyTelegramBotAPI).

jdatetime for Jalali (Shamsi) date support (install with pip install jdatetime).


Installation <a name="installation"></a>

1. Clone the repository:

git clone https://github.com/yourusername/telegram-pet-management-bot.git
cd telegram-pet-management-bot


2. Install the required Python libraries:

pip install -r requirements.txt


3. Set up environment variables: You need to store your bot token in an environment variable. To do this, run:

export BOT_TOKEN='your_telegram_bot_token'



Configuration <a name="configuration"></a>

In the bot, the following configurations are available:

Authorization: Add authorized users in the AUTHORIZED_USERS list in the Python script.

Example:

AUTHORIZED_USERS = [{'username': 'AdminUser', 'id': 123456789}]

Database: The bot uses an SQLite database (group_management.db) for storing members, payments, expenses, and pets.


Running the Bot <a name="running-the-bot"></a>

To run the bot, execute the following command:

python bot.py

The bot will start running and poll for new messages.

Restarting the Bot Automatically:

For better uptime and error handling, consider running the bot using Supervisor or systemd (as detailed in the "Error Handling and Polling" section).

Database Schema <a name="database-schema"></a>

The bot uses an SQLite database with the following schema:

Members Table: Stores member info and payment history.

CREATE TABLE IF NOT EXISTS Members (
    member_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    first_name TEXT,
    joined_date TEXT,
    last_payment_date TEXT,
    total_payments INTEGER DEFAULT 0
);

Pets Table: Stores pet details including name, type, breed, and associated costs.

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
);

Payments and Expenses Tables: Track payments made by members and group expenses.

CREATE TABLE IF NOT EXISTS Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount INTEGER,
    payment_date TEXT,
    FOREIGN KEY(member_id) REFERENCES Members(member_id)
);

CREATE TABLE IF NOT EXISTS Expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER,
    description TEXT,
    expense_date TEXT
);


Error Handling and Polling <a name="error-handling-and-polling"></a>

The bot uses bot.infinity_polling() for long-running processes. To ensure the bot automatically restarts after a crash, it's wrapped in a try-except block:

while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(5)

For production environments, it's recommended to use Supervisor or systemd to manage the bot and automatically restart it in case of failures.

Example with Supervisor:

1. Install supervisor:

sudo apt-get install supervisor


2. Create a configuration file for the bot:

[program:mybot]
command=python3 /path/to/your/bot.py
autostart=true
autorestart=true
stderr_logfile=/var/log/mybot.err.log
stdout_logfile=/var/log/mybot.out.log


3. Reload and start supervisor:

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mybot



Contributing <a name="contributing"></a>

If you'd like to contribute to the project, feel free to fork the repository and submit pull requests. Any help with bug fixes, new features, or improvements is welcome!
