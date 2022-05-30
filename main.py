import logging

from telegram.ext import CommandHandler, MessageHandler, \
    ApplicationBuilder, filters, CallbackQueryHandler

from tortoise import run_async

from database.init import init

from handlers.menu import CREATE_OR_UPDATE_CALLSIGN, start, callsign, \
    commit_callsign, stop_calsign
from handlers.admin_command import *

from settings.settings import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def unrecognized_message(update: Update,
                               context: CallbackContext.DEFAULT_TYPE) -> None:
    text = 'Нераспознанная команда.'
    await update.message.reply_text(text=text)


if __name__ == '__main__':
    # Init database connect
    run_async(init())

    # Create the app
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Create handlers
    start_handler = CommandHandler('start', start)
    unrec_message = MessageHandler(
        filters.TEXT & ~ filters.COMMAND, unrecognized_message
    )

    reg_handler = ConversationHandler(
        allow_reentry=True,
        entry_points=[CommandHandler('callsign', callsign)],
        states={
            CREATE_OR_UPDATE_CALLSIGN: [
                MessageHandler(filters.TEXT & (~ filters.COMMAND), commit_callsign)
            ]
        },
        fallbacks=[CommandHandler('cancel', stop_calsign)],
    )

    selection_handlers = [
        # editing_team,
        CallbackQueryHandler(adding_team, pattern="^" + str(ADD_TEAM) + "$"),
        CallbackQueryHandler(sum, pattern="^" + str(EDIT_TEAM) + "$"),
        CallbackQueryHandler(sum, pattern="^" + str(DELETE_TEAM) + "$"),
        CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
    ]
    admin_handler = ConversationHandler(
        allow_reentry=True,
        entry_points=[CommandHandler('admin', admin)],
        states={
            SELECTING_ACTION: selection_handlers,
            ENTERING_TEAM: [MessageHandler(
                filters.TEXT & ~ filters.COMMAND, commit_team
            )],
            STOPPING: [CommandHandler('admin', admin)]
        },
        fallbacks=[CommandHandler('stop', stop),
                   CommandHandler('callsign', callsign)]
    )

    application.add_handler(start_handler)
    application.add_handler(reg_handler)
    application.add_handler(admin_handler)
    application.add_handler(unrec_message)

    # Run the app
    application.run_polling()
