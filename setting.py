from tqdm import tqdm
from loguru import logger

import random
import time
import requests

# ========================
MODULE = 8
# ========================

IS_SLEEP = True  # True / False. True ���� ����� ��������� sleep ����� ����������
# �� ������� �� ������� ���� ����� ���������� (�������) :
SLEEP_FROM = 80
SLEEP_TO = 120

TRANSFER = False     # ������ �������� � ����� True = ��, False = ���
TRANSFER_DELAY = 60     # �������� ����� ��������� ������� � ���������� � ��������

DELAY_RETRY_FIND_BALANCE = 300  # �������� ����� ��������� ������� ������� � ��������

# ����� �� ��������������� (������������) ��������. True = ��. False = ���
RANDOM_WALLETS = True

RETRY = 0   # ���-�� ������� ��� ������� / ������

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

    # �������� from ����: [�������� ������, �������� ������, ...]
    from_chains = {'polygon': ['0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'],
                   'avalanche': ['0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E', '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7']}

    # �������� to ����: [�������� ������, �������� ������, ...]
    to_chains = {'polygon': ['0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'],
                 'avalanche': ['0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E', '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7']}

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
    # ����
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

    amount_from = 20                 # �� ������ ���-�� from_token �������
    amount_to = 30                   # �� ������ ���-�� from_token �������

    swap_all_balance = True        # True / False. ���� True, ����� ������� ���� ������
    min_amount_swap = 0             # ���� ������ ����� ������ ����� �����, ������� �� �����
    keep_value_from = 0         # �� ������� ����� ��������� �� �������� (�������� ������ ��� : swap_all_balance = True)
    keep_value_to = 0           # �� ������� ����� ��������� �� �������� (�������� ������ ��� : swap_all_balance = True)

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
    token_address = chains[chain]  # ����� ���� �������� ����� ����

    amount_from = 1  # �� ������ ���-�� ����� ������ ��������
    amount_to = 2  # �� ������ ���-�� ����� ������ ��������

    transfer_all_balance = False  # True / False. ���� True, ����� ������� ���� ������
    min_amount_transfer = 0  # ���� ������ ����� ������ ����� �����, �������� �� �����
    keep_value_from = 0  # �� ������� ����� ��������� �� �������� (�������� ������ ��� : transfer_all_balance = True)
    keep_value_to = 0  # �� ������� ����� ��������� �� �������� (�������� ������ ��� : transfer_all_balance = True)

    return chain, amount_from, amount_to, transfer_all_balance, min_amount_transfer, keep_value_from, keep_value_to, token_address

def value_1inch_swap(first, last, private_key):
    from utils import check_balance

    '''
    свапы на 1inch
    chains : ethereum | optimism | bsc | polygon | arbitrum | avalanche | fantom | zksync
    '''

    data_swap = {
        # 'avalanche': {
        #     'usdt' : '0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7',
        #     'usdc': '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',
        #     'native': '',
        #     'coins': {}
        # },
        'fantom': {
            'usdt' : '0x1B27A9dE6a775F98aaA5B90B62a4e2A0B84DbDd9',
            'usdc': '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75',
            'native_coin': 'ftm',
            'native_contract': '',
            'gas_balance': 5,
            'min_swap': 1, #минимальный свап
            'max_swap': 3,
            'coins': {
                'link': '0xb3654dc3D10Ea7645f8319668E8F54d2574FBdC8',
                'frax': '0xdc301622e621166BD8E82f2cA0A26c13Ad0BE355',
                'woo': '0x6626c47c00F1D87902fc13EECfaC3ed06D5E8D8a',
                #'cel': '0x2c78f1b70ccf63cdee49f9233e9faa99d43aa07e',
                'sushi': '0xae75A438b2E0cB8Bb01Ec1E1e376De11D44477CC',
                #'stg': '0x2f6f07cdcf3588944bf4c42ac74ff24bf56e7590',
                'aave': '0x6a07A792ab2965C72a5B8088d3a069A7aC3a993B',
                #'bifi': '0xd6070ae98b8069de6b494332d1a1a81b6179d960',
            },
        },
        'polygon': {
            'usdt': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', #контракт usdt
            'usdc': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', #контракт usdc
            'native_coin': 'matic', #нативная монета
            'native_contract': '', #контракт нативной монеты
            'gas_balance': 5, #минимальный остаток для газа
            'min_swap': 0.5, #минимальный свап
            'max_swap': 1, #максимальный свап
            'coins': { 
                'link': '0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39',
                'sand': '0xbbba073c31bf03b8acf7c28ef0738decf3695683',
                'woo': '0x1B815d120B3eF02039Ee11dC2d33DE7aA4a8C603',
                'bal': '0x9a71012b13ca4d3d0cdc72a177df3ef03b0e76a3',
                #'cel': '0xd85d1e945766fea5eda9103f918bd915fbca63e6',
                'sushi': '0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a',
                #'tel': '0xdf7837de1f2fa4631d716cf2502f8b230f1dcc32',
                'uni': '0xb33eaad8d922b1083446dc23f610c2567fb5180f',
                #'stg': '0x2f6f07cdcf3588944bf4c42ac74ff24bf56e7590',
                'aave': '0xd6df932a45c0f255f85145f286ea0b292b21c90b',
                #'bifi': '0xFbdd194376de19a88118e84E279b977f165d01b8',
            }
        }
    }

    min_swaps = {
        'link': 0.002,
        'sand': 0.2,
        'frax': 0.1,
        'woo': 0.4,
        'bal': 0.02,
        'cel': 0.4,
        'sushi': 0.1,
        'tel': 57,
        'uni': 0.02,
        'stg': 0.18,
        'aave': 0.002,
        'bifi': 0.0002,
    }
    
    chain = random.choice(list(data_swap.keys()))

    logger.info(f"chain : {chain}")

    amount_from         = 0.8    # от какого кол-ва монет свапаем в $
    amount_to           = 1.2    # до какого кол-ва монет свапаем в $
    slippage = 3 # слиппейдж, дефолт от 1 до 3

    from_symbol = ''
    to_symbol = ''
    from_token_address = ''
    to_token_address = ''


    if first:
        logger.info("First swap")
        balance_usdt = check_balance(private_key, chain, data_swap[chain]['usdt'])
        logger.info(f'balance_usdt : {balance_usdt}')
        balance_usdc = check_balance(private_key, chain, data_swap[chain]['usdc'])
        logger.info(f'balance_usdc : {balance_usdc}')

        from_token_address = ''

        if balance_usdt >= amount_to:
            from_symbol = 'usdt'
            from_token_address = data_swap[chain]['usdt']

        if balance_usdc >= amount_to:
            from_symbol = 'usdc'
            from_token_address = data_swap[chain]['usdc']

        if from_token_address == '':
            from_symbol = data_swap[chain]['native_coin']

        to_symbol = random.choice(list(data_swap[chain]['coins'].keys()))
        to_token_address = data_swap[chain]['coins'][to_symbol]

        return [[chain, amount_from, amount_to, from_token_address, to_token_address, slippage, from_symbol, to_symbol]]

    if last:
        ret = []
        logger.info("Last swap")
        
        for chain in data_swap.keys():
            to_symbol = 'usdc'
            to_token_address = data_swap[chain]['usdc']

            for coin in list(data_swap[chain]['coins'].keys()):
                balance = check_balance(private_key, chain, data_swap[chain]['coins'][coin])
                logger.info(f'balance {chain} {coin} : {balance}')
                
                if balance > min_swaps[coin]:
                    from_symbol = coin
                    from_token_address = data_swap[chain]['coins'][coin]
                    amount_from = balance
                    amount_to = balance

                    ret.append([chain, amount_from, amount_to, from_token_address, to_token_address, slippage, from_symbol, to_symbol])

            balance = check_balance(private_key, chain, data_swap[chain]['native_contract'])
            from_symbol = data_swap[chain]['native_coin']
            from_token_address = data_swap[chain]['native_contract']
            logger.info(f'balance {from_symbol} : {balance}')
            increased_gas_balance = data_swap[chain]['gas_balance'] * 1.2

            if balance > increased_gas_balance:
                amount_from = balance - data_swap[chain]['gas_balance']
                amount_to = amount_from
                ret.append([chain, amount_from, amount_to, from_token_address, to_token_address, slippage, from_symbol, to_symbol])
        return ret

    balance = check_balance(private_key, chain, data_swap[chain]['native_contract'])

    increased_gas_balance = data_swap[chain]['gas_balance'] * 1.5
    logger.info(f'balance {data_swap[chain]["native_coin"]} : {balance}. Increased gas balance: {increased_gas_balance}') 
    if balance > increased_gas_balance:
        from_symbol = data_swap[chain]['native_coin']
        from_token_address = data_swap[chain]['native_contract']
        available = balance - data_swap[chain]['gas_balance']
        amount_from = random.uniform(min(data_swap[chain]['min_swap'], available), min(available, data_swap[chain]['max_swap']))
        amount_to = amount_from
        to_symbol = random.choice(list(data_swap[chain]['coins'].keys()))
        to_token_address = data_swap[chain]['coins'][to_symbol]

        return [[chain, amount_from, amount_to, from_token_address, to_token_address, slippage, from_symbol, to_symbol]]
    
    from_symbol = ''
    for coin in list(data_swap[chain]['coins'].keys()):
        balance = check_balance(private_key, chain, data_swap[chain]['coins'][coin])
        logger.info(f'balance {coin} : {balance}')
        if balance > min_swaps[coin]:
                from_symbol = coin
                from_token_address = data_swap[chain]['coins'][coin]
                amount_from = balance
                amount_to = balance
                break
        
    if from_symbol == '':
        return value_1inch_swap(True, False, private_key)
        
    to_symbol = data_swap[chain]['native_coin']
    to_token_address = data_swap[chain]['native_contract']

    amount_from = balance
    amount_to = balance

    return [[chain, amount_from, amount_to, from_token_address, to_token_address, slippage, from_symbol, to_symbol]]
