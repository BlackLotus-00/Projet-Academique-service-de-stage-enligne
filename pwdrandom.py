from lib2to3.pygram import Symbols
import random
import string


def randomPwd(length):
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = string.digits

    all = lower + upper + num + '@'

    temp = random.sample(all,length)

    password = ''.join(temp)
    return password
    