from tqdm import tqdm

import random
import time
import requests

# ========================
MODULE = 8
# ========================

IS_SLEEP = True  # True / False. True если нужно поставить sleep между кошельками
# от скольки до скольки спим между кошельками (секунды) :
SLEEP_FROM = 80
SLEEP_TO = 120

TRANSFER = True     # Делать трансфер в конце True = да, False = нет
TRANSFER_DELAY = 18000     # Задержка между последним бриджем и трансфером в секундах

DELAY_RETRY_FIND_BALANCE = 300  # Задержка между повторным поиском баланса в секундах

# Нужно ли рандомизировать (перемешивать) кошельки. True = да. False = нет
RANDOM_WALLETS = True

RETRY = 0   # кол-во попыток при ошибках / фейлах

def convert_to_dollars(value, symbol):
    api_key = '7ca03b40-8627-4aa0-8325-83fccc97e8c5'
    api_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key
    }
    price = 1
    if(symbol == 'polygon'):
        params = {
            'symbol': 'MATIC',
            'convert': 'USD'
        }
        response = requests.get(api_url, params=params, headers=headers).json()
        price = response['data']['MATIC']['quote']['USD']['price']

    elif(symbol == 'fantom'):
        params = {
            'symbol': 'FTM',
            'convert': 'USD'
        }
        response = requests.get(api_url, params=params, headers=headers).json()
        price = response['data']['FTM']['quote']['USD']['price']

    elif(symbol == 'avalanche'):
        params = {
            'symbol': 'AVAX',
            'convert': 'USD'
        }
        response = requests.get(api_url, params=params, headers=headers).json()
        price = response['data']['AVAX']['quote']['USD']['price']


    return price

def value_woofi(privatekey, is_last=False):
    from utils import check_balance

    # название from сети: [контракт токена, контракт токена, ...]
    from_chains = {'polygon': ['0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'],
                   'fantom': ['0x04068DA6C83AFCFA0e13ba15A6696662335D5B75', '0x049d68029688eAbF473097a2fC38ef61633A3C7A'],
                   'avalanche': ['0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E', '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7'],
                   'bsc': ['0x55d398326f99059ff775485246999027b3197955']}

    # название to сети: [контракт токена, контракт токена, ...]
    to_chains = {'polygon': ['0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'],
                 'avalanche': ['0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E']}

    chain_with_balance = ''
    balance = 0
    contract_with_balance = ''
    while chain_with_balance == '':
        for chain, contracts in from_chains.items():
            for contract in contracts:
                cur_balance = check_balance(privatekey, chain, contract)


                if(contract == ''):
                    in_dollars = convert_to_dollars(cur_balance, chain)
                    cur_balance_in_dollars = in_dollars * cur_balance

                    if cur_balance_in_dollars > balance:
                        balance = cur_balance
                        chain_with_balance = chain
                        contract_with_balance = contract


                if cur_balance > balance:
                    balance = cur_balance
                    chain_with_balance = chain
                    contract_with_balance = contract

        if chain_with_balance == '':
            for _ in tqdm(range(DELAY_RETRY_FIND_BALANCE), desc='sleep (find balance ',
                          bar_format='{desc}: {n_fmt}/{total_fmt}'):
                time.sleep(1)
    # сети
    chains_list = list(to_chains)

    from_chain = chain_with_balance
    to_chain = chains_list[random.randint(0, len(chains_list)-1)]
    if not is_last:
        while to_chain == from_chain:
            to_chain = chains_list[random.randint(0, len(chains_list) - 1)]
    else:
        while to_chain == from_chain or to_chain not in ['polygon', 'avalanche']:
            to_chain = chains_list[random.randint(0, len(chains_list) - 1)]

    from_token = contract_with_balance
    to_token = to_chains[to_chain][random.randint(0, len(to_chains[to_chain])-1)]

    amount_from = 20                 # от какого кол-ва from_token свапаем
    amount_to = 30                   # до какого кол-ва from_token свапаем

    swap_all_balance = True        # True / False. если True, тогда свапаем весь баланс
    min_amount_swap = 0             # если баланс будет меньше этого числа, свапать не будет
    keep_value_from = 0.001         # от скольки монет оставляем на кошельке (работает только при : swap_all_balance = True)
    keep_value_to = 0.002           # до скольки монет оставляем на кошельке (работает только при : swap_all_balance = True)

    return from_chain, to_chain, from_token, to_token, swap_all_balance, amount_from, \
        amount_to, min_amount_swap, keep_value_from, keep_value_to


def value_transfer(privatekey):
    from utils import check_balance

    chains = {'polygon': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
              'fantom': '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75',
              'avalanche': '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E'}
    chain_with_balance = ''
    balance = 0
    while chain_with_balance == '':
        for chain, contract in chains.items():
            cur_balance = check_balance(privatekey, chain, contract)
            if cur_balance > balance:
                balance = cur_balance
                chain_with_balance = chain

        if chain_with_balance == '':
            for _ in tqdm(range(DELAY_RETRY_FIND_BALANCE), desc='sleep (find balance ',
                          bar_format='{desc}: {n_fmt}/{total_fmt}'):
                time.sleep(1)

    chain = chain_with_balance
    token_address = chains[chain]  # пусто если нативный токен сети

    amount_from = 1  # от какого кол-ва монет делаем трансфер
    amount_to = 2  # до какого кол-ва монет делаем трансфер

    transfer_all_balance = True  # True / False. если True, тогда выводим весь баланс
    min_amount_transfer = 0  # если баланс будет меньше этого числа, выводить не будет
    keep_value_from = 0  # от скольки монет оставляем на кошельке (работает только при : transfer_all_balance = True)
    keep_value_to = 0  # до скольки монет оставляем на кошельке (работает только при : transfer_all_balance = True)

    return chain, amount_from, amount_to, transfer_all_balance, min_amount_transfer, keep_value_from, keep_value_to, token_address