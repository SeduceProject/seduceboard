from __future__ import absolute_import, unicode_literals

import traceback
import sys
import os
import time
import threading
from core.data.snmp import get_connection_info_for_pdu
from threading import Timer
from core.data.snmp import get_pdus
from core.data.db import *
import telegram
import logging
from telegram.ext import Updater, CommandHandler
from core.config.bot_config import get_bot_configuration

logger = logging.getLogger('shipment_bot')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('shipment_bot.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)


CHECK_INTERVAL = 30
USER_IDS = []
NO_PAUSE = -1


def register(bot, update):
    global USER_IDS
    user_id = update.effective_user.id
    if not user_id in USER_IDS:
        msg = "You are now registered :-)"
        USER_IDS += [update.effective_user.id]
    else:
        msg = "You are already registered"
    logger.info(msg)
    update.message.reply_text(msg, parse_mode=telegram.ParseMode.HTML)


def unregister(bot, update):
    global USER_IDS
    global check_shipment_status
    user_id = update.effective_user.id
    if not user_id in USER_IDS:
        msg = "You are not registered"
    else:
        msg = "You are unregistered :-("
        USER_IDS = [x for x in USER_IDS if x != user_id]
    logger.info(msg)
    update.message.reply_text(msg, parse_mode=telegram.ParseMode.HTML)


def set_interval(f, args, interval_secs, task_name=None):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False

        def run(self):
            start_task_time = time.time()
            try:
                self.f(self.args)
            except Exception as e:
                traceback.print_exc()
                print("recovering an error")
            end_task_time = time.time()
            print("[sched:%s] took %f seconds to execute the task (starting: %f)" % (task_name, (end_task_time - start_task_time), start_task_time))
            time_to_sleep = (self.interval) - (end_task_time - start_task_time)
            if interval_secs != NO_PAUSE and time_to_sleep > 0:
                Timer(time_to_sleep, self.run).start()
            else:
                self.run()

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval_secs)
    t.start()
    return t


def check_ping(address):
    response = os.system("ping -c 1 " + address)
    # and then check the response...
    return response == 0


def check_hosts(args):
    for pdu_id in get_pdus():
        connection_info = get_connection_info_for_pdu(pdu_id)
        disconnected = True
        host = connection_info["pdu_ip"]
        for i in range(0, 5):
            if check_ping(host):
                disconnected = False
        logger.info("PING %s.disconnected -> %s" % (host, disconnected))
        if disconnected:
            for user_id in USER_IDS:
                bot.send_message(chat_id=user_id, text="PDU '%s' (%s) is disconnected" % (pdu_id, host))


if __name__ == "__main__":

    # Create a telegram bot
    token = get_bot_configuration().get("bot_token")
    bot = telegram.Bot(token=token)

    updater = Updater(token)
    updater.dispatcher.add_handler(CommandHandler('register', register))
    updater.dispatcher.add_handler(CommandHandler('unregister', unregister))

    # Create a thread in charge of checking hosts
    set_interval(check_hosts, (["None"]), 30, task_name="hosts_checker")

    # Start reading messages
    updater.start_polling()
    updater.idle()

    sys.exit(0)
