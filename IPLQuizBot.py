import logging

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot, Message, ChatAction
from telegram.ext import Updater, CommandHandler, Handler, MessageHandler, Filters, ConversationHandler, RegexHandler, CallbackQueryHandler, StringCommandHandler, PrefixHandler
from functools import wraps

QUESTION, OPTIONS, ANSWER = range(3)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)
opt_count = 0
quiz_dict = {}
options = ["" for x in range(4)]
answers = []
question_asked = 0
highscore_dict = {}
question_answered = []
bot = Bot('854613379:AAEq8EJn8L0wmJtDAO4JkuORDiwasou7G08')
LIST_OF_ADMINS = [495256027]
current_question_id = 0
timer = 15


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped
	
@restricted
def start(update, context):
	global question_asked
	global question_answered
	global quiz_dict
	question_asked = 0
	question_answered = []
	current_question_id = 0
	quiz_dict = {}
	update.message.reply_text('Welcome to IPL quiz bot! Enter a custom question here and press enter')
	return QUESTION

@restricted
def help(update, context):
    update.message.reply_text('Help!')

@restricted	
def post_question(update, context):
	text = update.message.text
	if text == 'done':
		update.message.reply_text("Quiz Created")
		return ConversationHandler.END
	else:
		quiz_dict[text] = []
		global options
		options = []
		update.message.reply_text('Yes! Question has been recorded, give your 4 options, press enter after each option')
		global opt_count
		opt_count = 0
		return OPTIONS

@restricted
def post_options(update, context):
	global opt_count
	opt_count = opt_count + 1
	text = update.message.text
	options.append(text)
	update.message.reply_text('Option {} recorded'.format(opt_count))
	
	if opt_count == 4:
		quiz_dict[list(quiz_dict.keys())[-1]] = options
		bot.send_message(update.message.chat_id, 'All options recorded. Enter the option number for the Answer, example 1, 2, 3 or 4')
		return ANSWER

@restricted		
def post_answer(update, context):	
	text = update.message.text
	global answers
	answers.append(text)
	bot.send_message(update.message.chat_id, 'Question {} created. Type your next Question or type '"done"' to create quiz'.format(len(quiz_dict.keys())))
	return QUESTION

@restricted
def start_quiz(update, context):
	global question_asked
	global question_answered
	global current_question_id
	question_asked = 0
	question_answered = []
	current_question_id = 0
	next_question(update, context)
	
@restricted
def next_question(update, context):
	global question_asked
	global question_answered
	global current_question_id
	if question_asked == int(len(quiz_dict.keys())):
		bot.delete_message(update.message.chat_id, current_question_id)
		bot.send_message(update.message.chat_id, 'Quiz Complete. Please wait for Admins to publish the result')
		publish_result()
		return
	if current_question_id != 0:
		bot.delete_message(update.message.chat_id, current_question_id)
	k = list(quiz_dict)[question_asked]
	v = list(quiz_dict.values())[question_asked]
	button_list = [
		[InlineKeyboardButton(v[0], callback_data="1")],
		 [InlineKeyboardButton(v[1], callback_data="2")],
		 [InlineKeyboardButton(v[2], callback_data="3")],
		 [InlineKeyboardButton(v[3], callback_data="4")]]
	question_asked = question_asked + 1
	question_answered = []		
	current_question = bot.send_message(update.message.chat_id, 'QUESTION {}: \n\n'.format(question_asked) + k, reply_markup=InlineKeyboardMarkup(button_list))
	current_question_id = current_question.message_id
	set_timer(update, context)
	
def process_response(update, context):
	query = update.callback_query
	user = query.from_user.id
	selection = query.data
	if user in question_answered:
		bot.answer_callback_query(query.id, 'You already answered!')
	else:	
		if int(answers[question_asked-1]) == int(selection):
			if user not in highscore_dict:
				highscore_dict[user] = 1
			else:
				highscore_dict[user] = highscore_dict[user] + 1
		question_answered.append(user)
		bot.answer_callback_query(query.id, 'Answer registered!')

def alarm(context):
	job = context.job
	bot.send_message(job.context.message.chat_id, text='Time is up!')
	next_question(job.context, context)

def set_timer(update, context):
	bot.send_message(update.message.chat_id, 'You time starts now!')
	due = int(timer)
	job = context.job_queue.run_once(alarm, due, context=update)
	
def	publish_result():
	sorted_highscore = sorted(highscore_dict, key=highscore_dict.get, reverse=True)
	xstr = lambda s: s or ""
	for key in sorted_highscore:
		username = bot.getChat(key).username if bot.getChat(key).username != None else xstr(bot.getChat(key).first_name) + xstr(bot.getChat(key).last_name)
		bot.send_message(495256027, 'UserName/Name: {}, Score {}'.format(username, highscore_dict[key]))
	
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    
	updater = Updater("854613379:AAEq8EJn8L0wmJtDAO4JkuORDiwasou7G08", use_context=True)
	dp = updater.dispatcher
	conv_handler = ConversationHandler(entry_points=[CommandHandler('start', start)],
		states={
			QUESTION: [MessageHandler(Filters.text, post_question, pass_user_data=True)],
			OPTIONS: [MessageHandler(Filters.text, post_options, pass_user_data=True)],
			ANSWER: [MessageHandler(Filters.text, post_answer, pass_user_data=True)]
		},

		fallbacks=[]
	)

	dp.add_handler(conv_handler)
	dp.add_handler(CommandHandler("help", help))
	dp.add_handler(CommandHandler('start_quiz', start_quiz))
	dp.add_handler(CommandHandler('nextquestion', next_question))
	dp.add_handler(CallbackQueryHandler(process_response, pass_user_data=True))
	dp.add_error_handler(error)

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
    main()