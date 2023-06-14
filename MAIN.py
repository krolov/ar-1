from utils import *
from debank import *

from threading import Timer
from logging.handlers import RotatingFileHandler

import random

def start_transfer_tries(privatekey):
    while transfer(privatekey) == False:
        sleeping(40,60)


if __name__ == "__main__":
    logger.add(RotatingFileHandler(filename='logs.txt'))
    is_first = True

    for _ in range(int(input('Кол-во циклов: '))-1):
        if RANDOM_WALLETS:
            random.shuffle(WALLETS)

        zero = 0
        for key in WALLETS:
            zero += 1

            wallet = evm_wallet(key)
            list_send.append(f'{zero}/{len(WALLETS)} : {wallet}\n')
            cprint(f'\n{zero}/{len(WALLETS)} : {wallet}\n', 'white')

            woofi(key)
            logger.info("bridge done")

            if is_first:
                with open('results/finished_wallets.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{key}\n')

            flip = random.randrange(1)#рандом 50%
            logger.info(f'flip: {flip}')
            if flip:
                delay = random.randint(60, 120) # время делея
                Timer(delay, inch_swap, kwargs={'privatekey': key, 'retry': 0}).start() # свап
                
            if IS_SLEEP:
                sleeping(SLEEP_FROM, SLEEP_TO) # таймаут

        if is_first:
            is_first = False
        
        print("Sleep")
        sleeping(86400, 94000)

    if RANDOM_WALLETS:
        random.shuffle(WALLETS)

    zero = 0
    for key in WALLETS:
        zero += 1

        wallet = evm_wallet(key)
        list_send.append(f'{zero}/{len(WALLETS)} : {wallet}\n')
        cprint(f'\n{zero}/{len(WALLETS)} : {wallet}\n', 'white')

        if TRANSFER:
            woofi(key, is_last=True)
            
            Timer(10, start_transfer_tries, kwargs={'privatekey': key}).start()
        else:
            woofi(key)

        delay = random.randint(120, 180) # время делея
        Timer(delay, inch_swap, kwargs={'privatekey': key, 'retry': 0, 'last': True}).start() # свап

        if is_first:
            with open('results/finished_wallets.txt', 'a', encoding='utf-8') as f:
                f.write(f'{key}\n')

        if IS_SLEEP:
            sleeping(SLEEP_FROM, SLEEP_TO)
