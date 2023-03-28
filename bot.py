from dotenv import load_dotenv
import os
from functools import wraps
import telebot
import pandas as pd
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

def is_known_username(username):
    '''
    Returns true only if the username is whitelisted.
    '''
    known_usernames = os.environ.get("ALLOWED_USERNAMES").split(",")

    return username in known_usernames

def private_access():
    """
    Restrict command access to users only in the known_usernames list.
    """
    def deco_restrict(f):

        @wraps(f)
        def f_restrict(message, *args, **kwargs):
            username = message.from_user.username

            if is_known_username(username):
                return f(message, *args, **kwargs)
            else:
                bot.reply_to(message, text='Sorry, this is a private bot!')

        return f_restrict  # true decorator

    return deco_restrict

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Hi, how may I help you?")

@bot.message_handler(commands=['help'])
@private_access()
def help_command(message):
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.add(
       telebot.types.InlineKeyboardButton(
           'Message the developer', url=os.environ.get("DEVELOPER_URL")
       )
   )
   bot.send_message(
       message.chat.id,
       '1) Type and send /hello or /start to start conversation.\n' +
       '2) Type /ask to get your question answered or just directly type and send your question.',
       reply_markup=keyboard
   )

@bot.message_handler(commands=['ask'])
@private_access()
def send_welcome(message):
    prompt = "What is your question?"
    sent_msg = bot.send_message(message.chat.id, prompt, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, process_query)

@bot.message_handler(func=lambda msg: True)
@private_access()
def user_input(message):
    process_query(message)

def process_query(message):
    questions = df["Question"].tolist()
    checker = TextBlob(message.text)
    question = checker.correct()
    questions.insert(0, question.string)
    tfidf_vectorizer = TfidfVectorizer(stop_words="english")
    sparse_matrix = tfidf_vectorizer.fit_transform(questions)
    cos_sim = cosine_similarity(sparse_matrix, sparse_matrix)
    answer = df["Answer"].iloc[cos_sim[0][1:].argmax()]
    bot.reply_to(message, answer, parse_mode="HTML")

if __name__ == "__main__":
    df = pd.read_csv("<insert path to CSV file here>", encoding = "utf-8", engine="pyarrow")
    bot.infinity_polling()