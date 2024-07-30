import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

# Replace with your actual Telegram bot token
bot_token = "7244688269:AAFqn6chSa0_71vk5wNrHqQYauTi97VlHWA"

# MongoDB connection details (replace with yours)
mongo_uri = "mongodb+srv://test-sequence:Tt5jdW2hrEHKVo6V@cluster0.l67ew2y.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Adjust if using a remote  connection
mongo_db_name = "seq"
mongo_collection_name = "users"

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client[mongo_db_name]
users_collection = db[mongo_collection_name]

# Initialize TeleBot instance
bot = telebot.TeleBot(bot_token)

# User data structure (stored in MongoDB)
class User:
    def __init__(self, user_id, username, name, total_sequences=0, files=[]):
        self.user_id = user_id
        self.username = username
        self.name = name
        self.total_sequences = total_sequences
        self.files = files

# Function to update user information in MongoDB
def update_user_info(user_id, username, name):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        users_collection.update_one({"user_id": user_id}, {"$set": {"username": username, "name": name}})
    else:
        user = User(user_id, username, name)
        users_collection.insert_one(user.__dict__)

# Function to retrieve user data from MongoDB
def get_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user

# Function to handle /start command
@bot.message_handler(commands=["start"])
def start_message(message):
    user_id = message.from_user.id
    username = message.from_user.username
    name = message.from_user.first_name

    update_user_info(user_id, username, name)

    welcome_text = f"Welcome, {name}! I am a file sequencing bot.\n\n"
    bot_description = "Here's how to use me:\n\n" \
                      "1. Use the command /ssequence to begin a file sequencing process.\n" \
                      "2. Send the files you want to sequence.\n" \
                      "3. When you're done, use /esequence to finish and get the sequenced files.\n" \
                      "4. Use /cancel to cancel ongoing sequencing process.\n\n"
    additional_info = "Powered By: @STERN_LEGION"

    message_text = welcome_text + bot_description + additional_info

    keyboard = InlineKeyboardMarkup()
    developer_button = InlineKeyboardMarkup(text="DEVELOPER", url="https://t.me/JustMe_Charz")
    keyboard.add(developer_button)

    bot.send_message(message.chat.id, message_text, reply_markup=keyboard)

# Function to handle file processing
def process_file_sequence(message, file_type):
    user_id = message.from_user.id

    user = get_user(user_id)
    if user is None:
        bot.reply_to(message, "You haven't started a sequencing process yet. Use /ssequence first.")
        return

    file = getattr(message, file_type)

    if file:
        user.files.append(message) # Assuming 'files' is a list within the User object
        users_collection.update_one({"user_id": user_id}, {"$set": {"files": user.files}})
    else:
        bot.reply_to(message, "Unsupported file type. Send documents or videos.")

# Function to handle /endsequence command
@bot.message_handler(commands=["endsequence"])
def end_sequence(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if user in None or not user.files:
        bot.reply_to(message, "No files to sequence. Send some files with /ssequence first.")
        return
        
    user.files.sort(key=lambda file: file.document.file_name if hasattr(file, 'document') else file.video.file_name)

    for file_message in user.files:
        file = file_message.document or file_message.video
        caption = file_message.caption or ''

        if file_message.document:
            bot.send_document(message.chat.id, file.file-id, caption=caption)
        elif file_message.video:
            bot.send_video(message.chat.id, file.file_id, caption=caption)

    bot.reply_to(message, f"File sequencing completed. You have received {len(user.files)} sequenced files. Use /ssequence to start sequencing again.")

    user.total_sequences += len(user.files)
    users_collection.update_one({"user_id": user_id}, {"$set": {"total_sequences": user.total_sequences, "files": []}})

# Function to handle /stats command
@bot.message_handler(commands=["stats"])
def show_stats(message):
    total_users = users_collection.count_documents()
    total_sequences = users_collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total_sequences"}}}])
    total_sequences = list(total_sequences)[0].get("total", 0)

    bot.reply_to(message, f"Total Users: {total_users}\nTotal File Sequences: {total_sequences}")

# Handle document and video files
@bot.message_handler(content_types=['document', 'video'])
def handle_file(message):
    file_type = 'document' if message.document else 'video'
    process_file_sequence(message, file_type)

# Start the bot
bot.infinity_polling()
