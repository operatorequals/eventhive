import logging
import sys

try:
    from termcolor import colored
except ImportError:
    colored = lambda *args, **kwargs: args[0]

logger = logging.getLogger('eventhive')
logger.addHandler(logging.NullHandler())
# logger.addHandler(logging.StreamHandler(sys.stderr))


def add_notation(log_record):

    if log_record.levelno == logging.DEBUG:
        log_record.msg = colored("[%] ", "cyan") + log_record.msg

    elif log_record.levelno == logging.INFO:
        log_record.msg = colored("[+] ", "light_green") + log_record.msg

    elif log_record.levelno == logging.WARNING:
        log_record.msg = colored("[*] ", "yellow") + log_record.msg

    elif log_record.levelno == logging.ERROR:
        log_record.msg = colored("[!] ", "red") + \
            colored(log_record.msg, attrs=['underline'])

    elif log_record.levelno == logging.CRITICAL:
        log_record.msg = colored("[-] ", "red") + \
            colored(log_record.msg, "red", attrs=['bold'])

    return log_record


logger.addFilter(add_notation)


def test():
    logger.setLevel(logging.DEBUG)
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")
