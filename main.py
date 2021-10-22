import apiai, configparser, json, logging, telegram 
from telegram.ext import CallbackQueryHandler, CommandHandler, Dispatcher, Filters, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from flask import Flask, request

#Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

#Enable logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Initial Flask app
app = Flask(__name__)

#Initial bot by Telegram access token
bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))

#Declare welcome message
welcome_message = "Hi. My name is ComfortBot." + "\n" + "I can help you to relieve your stress." + "\n" + "If you unhappy, please tell me."
menu = ReplyKeyboardMarkup([['Tell me a joke'],
                            ['Play game'],
                            ['Hello']])

#Declare the Today's Mood test
happiness = ["angry", "sad", "OK", "pleased", "happy"]
emoji = {
	"angry": "😠",
	"sad": "☹",
	"OK": "😐",
	"pleased": "😀",
	"happy": "😁"
}

#Set route /hook with POST method will trigger this method to handle Webhooks request
@app.route('/hook', methods=['POST'])
def webhook_handler():
	if request.method == "POST":
		update = telegram.Update.de_json(request.get_json(force=True), bot)
		dispatcher.process_update(update)
	return 'ok'

#Method to handle /start command
def start_handler(bot, update):
	#Send Welcome message and menu to greet the user
	update.message.reply_text(welcome_message, reply_markup=menu)
	#Send sticker to user to enhance the humanity and more interesting
	bot.send_sticker(chat_id=update.message.chat_id, sticker='CAACAgEAAxkBAAIB-V6nu8Z1fnULBN_ezAHV1EcGJCNHAALxAANsWx0cr3uUHRQ0arcZBA')
	#Send Today's Mood test to keep user engagement
	update.message.reply_text("How do you feel today?",
		reply_markup = InlineKeyboardMarkup([[
        	InlineKeyboardButton(emoji, callback_data = happiness) for happiness, emoji in emoji.items()
        ]])
	)

#Method to handle the Today's Mood test
def mood_handler(bot, update):
	try:
		mood = update.callback_query.data
		if mood == "angry" or mood == "sad":
			update.callback_query.edit_message_text("Oh! I'm surprised that you feel {}. 😯\nCan you tell me why?".format(mood))
		elif mood == "OK" or mood == "pleased" or mood == "happy":
			update.callback_query.edit_message_text("I'm glad that you feel {}. 😀".format(mood))
	except Exception as e:
		print(e)

#Method to handle the message sent by user
def reply_handler(bot, update):
	text = update.message.text
	#Basic greeting handle
	if text == "你好" or text == "Hi" or text == "hi" or text == "HI" or text == "Hello":
		reply = 'Hello, {}'.format(update.message.from_user.full_name)
	elif "game" in text: #If message contains "game", show the official game bot of Telegram with an InlineKeyboardButton
		reply = ''
		update.message.reply_text("Press the following button, there are lots of funny game!",
			reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Gamee", url = "https://telegram.me/gamee")]]))
	elif "joke" in text: #If message contains "joke", request Dialogflow for agent handling jokes
		try:
			client = apiai.ApiAI((config['JOKES']['CLIENT_ACCESS_TOKEN']))
			request = client.text_request()
			request.query = text
			response = request.getresponse()
			#Decode the json returned
			replyjson = json.loads(response.read().decode())
			reply = replyjson.get("result").get("fulfillment").get("speech")
		except:
			reply = "Sorry but DialogFlow API fail, please try again later."
	else: #Otherwise, request Dialogflow for agent handling small-talk
		try:
			client = apiai.ApiAI((config['SMALLTALK']['CLIENT_ACCESS_TOKEN']))
			request = client.text_request()
			request.query = text
			response = request.getresponse()
			#Decode the json returned
			replyjson = json.loads(response.read().decode())
			reply = replyjson.get("result").get("fulfillment").get("speech")
		except:
			reply = "Sorry but DialogFlow API fail, please try again later."
	update.message.reply_text(reply)

#Create a dispatcher for bot
dispatcher = Dispatcher(bot, None)

#Add handler for handling message
dispatcher.add_handler(CommandHandler('start', start_handler))
dispatcher.add_handler(CallbackQueryHandler(mood_handler))
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

#Default run the server
if __name__ == "__main__":
	app.run()