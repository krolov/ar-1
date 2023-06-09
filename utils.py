from config import *

list_send = []

networks2 = {
    "ethereum": {
        "USDC": 1,
        "USDt": 2,
        "USDT": 2,
        "DAI": 3,
        "FRAX": 7,
        "USDD": 11,
        "ETH": 13,
        "sUSD": 14,
        "LUSD": 15,
        "MAI": 16,
        "METIS": 17,
        "metis.USDT": 19
    },
    "bsc": {
        "USDt": 2,
        "USDT": 2,
        "BUSD": 5,
        "USDD": 11,
        "MAI": 16,
        "METIS": 17,
        "metis.USDT": 19
    },
    "avalanche": {
        "USDC": 1,
        "USDt": 2,
        "USDT": 2,
        "FRAX": 7,
        "MAI": 16,
        "metis.USDT": 19
    },
    "polygon": {
        "USDC": 1,
        "USDt": 2,
        "USDT": 2,
        "DAI": 3,
        "MAI": 16
 },
    "arbitrum": {
        "USDC": 1,
        "USDt": 2,
        "USDT": 2,
        "FRAX": 7,
        "ETH": 13,
        "LUSD": 15,
        "MAI": 16
    },
    "optimism": {
        "USDt": 1,
        "USDT": 1,
        "DAI": 3,
        "FRAX": 7,
        "ETH": 13,
        "sUSD": 14,
        "LUSD": 15,
        "MAI": 16
    },
}


# ============ web3_helpers ============
def evm_wallet(key):

    try:
        web3 = Web3(Web3.HTTPProvider(DATA['ethereum']['rpc']))
        wallet = web3.eth.account.from_key(key).address
        return wallet
    except:
        return key


def sign_tx(web3, contract_txn, privatekey):

    signed_tx = web3.eth.account.sign_transaction(contract_txn, privatekey)
    raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash = web3.to_hex(raw_tx_hash)
    
    return tx_hash


def check_data_token(web3, token_address):

    try:

        token_contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        decimals        = token_contract.functions.decimals().call()
        symbol          = token_contract.functions.symbol().call()

        return token_contract, decimals, symbol
    
    except Exception as error:
        logger.error(error)

def check_data_token_chain(chain, token_address):

    try:

        web3 = Web3(Web3.HTTPProvider(DATA[chain]['rpc']))
        token_contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        decimals        = token_contract.functions.decimals().call()
        symbol          = token_contract.functions.symbol().call()

        return token_contract, decimals, symbol
    
    except Exception as error:
        logger.error(error)


def check_status_tx(chain, tx_hash):

    logger.info(f'{chain} : checking tx_status : {tx_hash}')

    start_time_stamp = int(time.time())

    while True:
        try:

            rpc_chain   = DATA[chain]['rpc']
            web3        = Web3(Web3.HTTPProvider(rpc_chain))
            status_     = web3.eth.get_transaction_receipt(tx_hash)
            status      = status_["status"]

            if status in [0, 1]:
                return status

        except Exception as error:
            # logger.info(f'error, try again : {error}')
            time_stamp = int(time.time())
            if time_stamp-start_time_stamp > max_time_check_tx_status:
                logger.info(f'не получили tx_status за {max_time_check_tx_status} sec, думаем что tx is success')
                return 1
            time.sleep(1)


def add_gas_limit(web3, contract_txn):

    try:
        value = contract_txn['value']
        contract_txn['value'] = 0
        pluser = [1.02, 1.05]
        gasLimit = web3.eth.estimate_gas(contract_txn)
        contract_txn['gas'] = int(gasLimit * random.uniform(pluser[0], pluser[1]))
        # logger.info(f"gasLimit : {contract_txn['gas']}")
    except Exception as error: 
        contract_txn['gas'] = random.randint(2000000, 3000000)
        logger.info(f"estimate_gas error : {error}. random gasLimit : {contract_txn['gas']}")

    contract_txn['value'] = value
    return contract_txn


def add_gas_limit_layerzero(web3, contract_txn):

    try:
        pluser = [1.05, 1.07]
        gasLimit = web3.eth.estimate_gas(contract_txn)
        contract_txn['gas'] = int(gasLimit * random.uniform(pluser[0], pluser[1]))
        # logger.info(f"gasLimit : {contract_txn['gas']}")
    except Exception as error: 
        contract_txn['gas'] = random.randint(2000000, 3000000)
        logger.info(f"estimate_gas error : {error}. random gasLimit : {contract_txn['gas']}")

    return contract_txn


def add_gas_price(web3, contract_txn):

    try:
        gas_price = web3.eth.gas_price
        contract_txn['gasPrice'] = int(gas_price * random.uniform(1.01, 1.02))
    except Exception as error: 
        logger.error(error)

    return contract_txn


def round_to(num, digits=3):
    try:
        if num == 0: return 0
        scale = int(-math.floor(math.log10(abs(num - int(num))))) + digits - 1
        if scale < digits: scale = digits
        return round(num, scale)
    except: return num


def check_balance(privatekey, chain, address_contract):
    try:

        rpc_chain   = DATA[chain]['rpc']
        web3        = Web3(Web3.HTTPProvider(rpc_chain))

        try     : wallet = web3.eth.account.from_key(privatekey).address
        except  : wallet = privatekey
            
        if address_contract == '': # eth
            balance         = web3.eth.get_balance(web3.to_checksum_address(wallet))
            token_decimal   = 18
        else:
            token_contract, token_decimal, symbol = check_data_token(web3, address_contract)
            balance = token_contract.functions.balanceOf(web3.to_checksum_address(wallet)).call()

        human_readable = decimalToInt(balance, token_decimal) 

        # cprint(human_readable, 'blue')

        return human_readable

    except Exception as error:
        logger.error(error)
        time.sleep(1)
        check_balance(privatekey, chain, address_contract)


def check_allowance(chain, token_address, wallet, spender):

    try:
        web3 = Web3(Web3.HTTPProvider(DATA[chain]['rpc']))
        contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        amount_approved = contract.functions.allowance(wallet, spender).call()
        return amount_approved
    except Exception as error:
        logger.error(error)

# ============== modules ==============


def approve_(amount, privatekey, chain, token_address, spender, retry=0):

    try:

        web3 = Web3(Web3.HTTPProvider(DATA[chain]['rpc']))
        # web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        spender = Web3.to_checksum_address(spender)

        wallet = web3.eth.account.from_key(privatekey).address
        contract, decimals, symbol = check_data_token(web3, token_address)

        module_str = f'approve : {symbol}'

        allowance_amount = check_allowance(chain, token_address, wallet, spender)

        if amount > allowance_amount:

            contract_txn = contract.functions.approve(
                spender,
                115792089237316195423570985008687907853269984665640564039457584007913129639935
                ).build_transaction(
                {
                    "chainId": web3.eth.chain_id,
                    "from": wallet,
                    "nonce": web3.eth.get_transaction_count(wallet),
                    'gasPrice': 0,
                    'gas': 0,
                    "value": 0
                }
            )

            contract_txn = add_gas_price(web3, contract_txn)
            contract_txn = add_gas_limit(web3, contract_txn)

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash)

            if status == 1:
                logger.success(f"{module_str} | {tx_link}")
            else:
                logger.error(f"{module_str} | tx is failed | {tx_link}")
                if retry < RETRY:
                    logger.info(f"try again in 10 sec.")
                    sleeping(10, 10)
                    approve_(privatekey, chain, token_address, spender, retry+1)

    except Exception as error:
        logger.error(f'{error}')
        if retry < RETRY:
            logger.info(f'try again in 10 sec.')
            sleeping(10, 10)
            approve_(privatekey, chain, token_address, spender, retry+1)


def woofi_get_min_amount(chain, from_token, to_token, amount):

    try:

        if from_token.upper() != to_token.upper():

            # cprint(f'{chain} : {from_token} => {to_token} | {amount}', 'blue')

            slippage = 5

            web3 = Web3(Web3.HTTPProvider(DATA[chain]['rpc']))
            address_contract = web3.to_checksum_address(WOOFI_SWAP_CONTRACTS[chain])
            contract = web3.eth.contract(address=address_contract, abi=ABI_WOOFI_SWAP)

            from_token  = Web3.to_checksum_address(from_token)
            to_token    = Web3.to_checksum_address(to_token)

            minToAmount = int(amount - (amount * (slippage / 1000)))

            return minToAmount
        
        else:

            return int(amount)
    
    except Exception as error:
        logger.error(f'error : {error}. return 0')
        return 0


def woofi_bridge(privatekey, from_chain, to_chain, from_token, to_token, swap_all_balance, amount_from,
                 amount_to, min_amount_swap, keep_value_from, keep_value_to, retry=0, is_last=False):
    try:

        def get_srcInfos(amount_, from_chain, from_token):

            web3 = Web3(Web3.HTTPProvider(DATA[from_chain]['rpc']))

            from_token = Web3.to_checksum_address(from_token)

            if from_token != '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE':
                token_contract, decimals, symbol = check_data_token(web3, from_token)
            else: decimals = 18

            amount = intToDecimal(amount_, decimals)
            bridgeToken = WOOFI_PATH[from_chain]
            minBridgeAmount = woofi_get_min_amount(from_chain, from_token, WOOFI_PATH[from_chain], amount)

            from_token = Web3.to_checksum_address(from_token)
            bridgeToken = Web3.to_checksum_address(bridgeToken)

            srcInfos = [
                from_token,
                bridgeToken,
                amount,
                minBridgeAmount
            ]

            return srcInfos

        def get_dstInfos(amount, to_chain, to_token):

            chainId     = LAYERZERO_CHAINS_ID[to_chain]

            minToAmount = int(woofi_get_min_amount(to_chain, WOOFI_PATH[to_chain], to_token, amount) * 0.99)
            bridgeToken = WOOFI_PATH[to_chain]

            bridgeToken = Web3.to_checksum_address(bridgeToken)
            to_token    = Web3.to_checksum_address(to_token)

            dstInfos = [
                chainId,
                to_token,       # toToken
                bridgeToken,    # bridgeToken
                minToAmount,    # minToAmount
                0               # airdropNativeAmount
            ]

            return dstInfos

        module_str = f'woofi_bridge : {from_chain} => {to_chain}'
        logger.info(module_str)

        keep_value = round(random.uniform(keep_value_from, keep_value_to), 8)
        if swap_all_balance:
            if from_token == '':
                amount_ = check_balance(privatekey, from_chain, from_token)
                if from_chain == 'polygon':
                    amount_ *= 0.95
                elif from_chain == 'avalanche' or from_chain == 'bsc':
                    amount_ *= 0.95
                elif from_chain == 'fantom':
                    amount_ *= 0.95
                amount_ -= keep_value
            else:
                amount_ = check_balance(privatekey, from_chain, from_token) - keep_value
        else:
            amount_ = round(random.uniform(amount_from, amount_to), 8)

        web3 = Web3(Web3.HTTPProvider(DATA[from_chain]['rpc']))
        web3_tar = Web3(Web3.HTTPProvider(DATA[to_chain]['rpc']))

        address_contract = web3.to_checksum_address(
            WOOFI_BRIDGE_CONTRACTS[from_chain]
        )

        if from_token != '':
            token_contract, decimals, symbol = check_data_token(web3, from_token)
        else:
            decimals = 18

        contract    = web3.eth.contract(address=address_contract, abi=ABI_WOOFI_BRIDGE)
        wallet      = web3.eth.account.from_key(privatekey).address

        if to_token     == '' : to_token    = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
        if from_token   == '' : from_token  = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'

        amount      = intToDecimal(amount_, decimals)
        srcInfos    = get_srcInfos(amount_, from_chain, from_token)

        if from_chain == 'bsc':
            amount_src = decimalToInt(srcInfos[3], 18)
            amount_src = intToDecimal(amount_src, 6)
        else:
            amount_src = srcInfos[3]

        dstInfos    = get_dstInfos(amount_src, to_chain, to_token)

        # cprint(f'\nsrcInfos : {srcInfos}\ndstInfos : {dstInfos}', 'blue')

        # если токен не нативный, тогда проверяем апрув и если он меньше нужного, делаем апруваем
        if from_token != '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE':
            approve_(amount, privatekey, from_chain, from_token, WOOFI_BRIDGE_CONTRACTS[from_chain])
            sleeping(5, 10)


        # TODO MODED CODE START
        while True:
            try:
                fees = contract.functions.quoteLayerZeroFee(
                    dstInfos[0],  # dst chain
                    1,  # function type (1 - swap, 2 - add Liquidity, 3 - REDEEM LOCAL CALL BACK, 4 - WITHDRAW REMOTE)
                    dstInfos[1],  # to address
                    "0x",  # payload, using abi.encode()

                    # lz Tx Params
                    [0,  # extra gas, if calling smart contract
                     0,  # amount of dust dropped in destination wallet
                     "0x0000000000000000000000000000000000000001"  # destination wallet for dust
                     ]
                    ).call()
                break
            except Exception as error:
                logger.error(error)
                time.sleep(1)

        if from_token == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE':
            value = int(amount + fees[0])
        else:
            value = int(fees[0])


        token_contract2, decimals2, symbol2 = check_data_token(web3, from_token)
        token_contract3, decimals3, symbol3 = check_data_token(web3_tar, to_token)

        src_pool = 1
        tar_pool = 1

        if from_chain in networks2.keys():
            src_pool = networks2[from_chain][symbol2] if symbol2 in networks2[from_chain].keys() else None


        if to_chain in networks2.keys():
            tar_pool = networks2[to_chain][symbol3] if symbol3 in networks2[to_chain].keys() else None

        amount_ = amount
        min_amount_swap = dstInfos[3]

        if amount_ >= min_amount_swap:
            contract_txn = contract.functions.swap(
                dstInfos[0],
                src_pool,
                tar_pool,# refId
                wallet,     # to
                amount_,
                min_amount_swap,
                [
                    0,  # dst Gas For Call
                    0,  # dst Native Amount
                    wallet  # dst Native Addr
                ],
                wallet,
                '0x'
                ).build_transaction(
                {
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'value': value,
                    'gasPrice': 0,
                    'gas': 0,
                }
            )

            # TODO MODED CODE END

            contract_txn = add_gas_price(web3, contract_txn)
            contract_txn = add_gas_limit_layerzero(web3, contract_txn)

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[from_chain]["scan"]}/{tx_hash}'

            status = check_status_tx(from_chain, tx_hash)

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                time.sleep(3)

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')

                retry += 1
                if retry < RETRY:
                    logger.info(f'try again | {wallet}')
                    time.sleep(3)
                    woofi_bridge(privatekey, from_chain, to_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to, retry+1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')

        else:
            logger.error(f"{module_str} : can't bridge : {amount_} (amount) < {min_amount_swap} (min_amount_swap)")
            list_send.append(f'{STR_CANCEL}{module_str} : {amount_} < {min_amount_swap}')

    except Exception as error:
        logger.error(f'{module_str} | error : {error}')
        if retry < RETRY:
            logger.info(f'try again in 10 sec.')
            sleeping(10, 10)
            woofi_bridge(privatekey, from_chain, to_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')


def woofi_swap(privatekey, from_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to, retry=0):

    try:

        module_str = f'woofi_swap : {from_chain}'
        logger.info(module_str)

        keep_value = round(random.uniform(keep_value_from, keep_value_to), 8)
        if swap_all_balance:
            if from_token == '':
                amount_ = check_balance(privatekey, from_chain, from_token)
                if from_chain == 'polygon':
                    amount_ *= 0.95
                elif from_chain == 'avalanche' or from_chain == 'bsc':
                    amount_ *= 0.95
                elif from_chain == 'fantom':
                    amount_ *= 0.95
                amount_ -= keep_value
            else:
                amount_ = check_balance(privatekey, from_chain, from_token) - keep_value
        else:
            amount_ = round(random.uniform(amount_from, amount_to), 8)
            
        web3 = Web3(Web3.HTTPProvider(DATA[from_chain]['rpc']))
        address_contract = web3.to_checksum_address(
            WOOFI_SWAP_CONTRACTS[from_chain]
        )

        from_token = Web3.to_checksum_address(from_token)
        to_token    = Web3.to_checksum_address(to_token)

        if from_token != '':
            token_contract, decimals, symbol = check_data_token(web3, from_token)
        else:
            decimals = 18

        contract = web3.eth.contract(address=address_contract, abi=ABI_WOOFI_SWAP)
        wallet = web3.eth.account.from_key(privatekey).address

        amount = intToDecimal(amount_, decimals)

        # если токен не нативный, тогда проверяем апрув и если он меньше нужного, делаем апруваем
        if from_token != '':
            approve_(amount, privatekey, from_chain, from_token, WOOFI_SWAP_CONTRACTS[from_chain])
            sleeping(5, 10)

        if to_token == '':
            to_token = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
        if from_token == '':
            from_token = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
            value = amount
        else:
            value = 0





        # TODO MODED CODE START
        token_contract2, decimals2, symbol2 = check_data_token(web3, from_token)
        token_contract3, decimals3, symbol3 = check_data_token(web3, to_token)

        src_pool = 1
        tar_pool = 1

        if from_chain in networks2.keys():
            src_pool = networks2[from_chain][symbol2] if symbol2 in networks2[from_chain].keys() else None
            tar_pool = networks2[from_chain][symbol3] if symbol3 in networks2[from_chain].keys() else None

        else:
            print("Chain not available")

        minToAmount = woofi_get_min_amount(from_chain, from_token, to_token, amount)

        if amount_ >= min_amount_swap:
            contract_txn = contract.functions.swap(
                LAYERZERO_CHAINS_ID[from_chain],
                src_pool,
                tar_pool,
                wallet,
                amount, 
                minToAmount, 
                [
                    0,  # dst Gas For Call
                    0,  # dst Native Amount
                    wallet  # dst Native Addr
                ],
                wallet,
                '0x'
                ).build_transaction(
                {
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'value': value,
                    'gasPrice': 0,
                    'gas': 0,
                }
            )
        # TODO MODED CODE END


            contract_txn = add_gas_price(web3, contract_txn)
            contract_txn = add_gas_limit(web3, contract_txn)

            if swap_all_balance:
                if from_token == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE':
                    gas_gas = int(contract_txn['gas'] * contract_txn['gasPrice'])
                    contract_txn['value'] = contract_txn['value'] - gas_gas

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[from_chain]["scan"]}/{tx_hash}'

            status = check_status_tx(from_chain, tx_hash)
            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                time.sleep(3)

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                retry += 1
                if retry < RETRY:
                    logger.info(f'try again | {wallet}')
                    time.sleep(3)
                    woofi_swap(privatekey, from_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to, retry+1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')

        else:
            logger.error(f"{module_str} : can't swap : {amount_} (amount) < {min_amount_swap} (min_amount_swap)")
            list_send.append(f'{STR_CANCEL}{module_str} : {amount_} < {min_amount_swap}')

    except Exception as error:
        logger.error(f'{module_str} | error : {error}')
        if retry < RETRY:
            logger.info(f'try again in 10 sec.')
            sleeping(10, 10)
            woofi_swap(privatekey, from_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')


def woofi(privatekey, is_last=False):
    from_chain, to_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to = value_woofi(privatekey, is_last=is_last)
    if from_chain == None:
        return

    if from_chain == to_chain:
        woofi_swap(privatekey, from_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to)
    else:
        woofi_bridge(privatekey, from_chain, to_chain, from_token, to_token, swap_all_balance, amount_from, amount_to, min_amount_swap, keep_value_from, keep_value_to)


def transfer(privatekey, retry=0):
    try:

        to_address = RECIPIENTS_WALLETS[privatekey]
        chain, amount_from, amount_to, transfer_all_balance, min_amount_transfer, keep_value_from, keep_value_to, token_address = value_transfer(privatekey)

        keep_value = round(random.uniform(keep_value_from, keep_value_to), 8)

        module_str = f'transfer => {to_address}'

        web3 = Web3(Web3.HTTPProvider(DATA[chain]['rpc']))

        account = web3.eth.account.from_key(privatekey)
        wallet = account.address
        nonce = web3.eth.get_transaction_count(wallet)

        if token_address == '':
            decimals = 18
            symbol = DATA[chain]['token']
        else:
            token_contract, decimals, symbol = check_data_token(web3, token_address)

        if transfer_all_balance:
            amount = (check_balance(privatekey, chain, token_address) - keep_value) * 0.97
        else:
            amount = round(random.uniform(amount_from, amount_to), 8)

        value = intToDecimal(amount, decimals)

        if amount >= min_amount_transfer:

            if token_address == '':

                contract_txn = {
                    'chainId': web3.eth.chain_id,
                    'gasPrice': 0,
                    'nonce': nonce,
                    'gas': 0,
                    'to': Web3.to_checksum_address(to_address),
                    'value': int(value)
                }

            else:

                tx = {
                    'chainId': web3.eth.chain_id,
                    'gasPrice': 0,
                    'gas': 0,
                    'nonce': nonce,
                }

                contract_txn = token_contract.functions.transfer(
                    Web3.to_checksum_address(to_address),
                    int(value)
                ).build_transaction(tx)

            contract_txn = add_gas_price(web3, contract_txn)
            contract_txn = add_gas_limit(web3, contract_txn)

            if token_address == '':
                if transfer_all_balance:
                    gas_price = contract_txn['gasPrice']
                    gas_limit = contract_txn['gas']
                    gas_gas = gas_price * gas_limit
                    contract_txn['value'] = int(value) - int(gas_gas)

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            module_str = f'transfer {round_to(amount)} {symbol} => {to_address}'

            status = check_status_tx(chain, tx_hash)
            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
            else:
                if retry < RETRY:
                    logger.info(f'{module_str} | tx is failed, try again in 10 sec | {tx_link}')
                    sleeping(10, 10)
                    transfer(privatekey, retry + 1)
                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')

        else:
            logger.error(
                f"{module_str} : can't transfer : {amount} (amount) < {min_amount_transfer} (min_amount_transfer)")
            list_send.append(f'{STR_CANCEL}{module_str} : {amount} < {min_amount_transfer}')

    except Exception as error:

        logger.error(f'{module_str} | {error}')
        if retry < RETRY:
            logger.info(f'try again | {wallet}')
            sleeping(10, 10)
            transfer(privatekey, retry + 1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def get_api_call_data(url):

    def try_get_with_proxy():
        try:
            proxy = random.choice(PROXIES)
            # cprint(proxy, 'yellow')
            proxies = {
                'http'  : proxy,
                'https' : proxy,
            }
            call_data = requests.get(url, proxies=proxies)
            return call_data
        except Exception as error:
            logger.error(error)
            call_data = requests.get(url)

    call_data = requests.get(url)

    # cprint(f'call_data.status_code : {call_data.status_code}', 'blue')

    if call_data.status_code == 200:
        api_data = call_data.json()
        return api_data
    
    raise Exception(f'call_data.status_code : {call_data.status_code}')
    # throw error
    


    # else:

    #     logger.info(call_data.content)

    #     call_data = try_get_with_proxy()

    #     if call_data.status_code == 200:
    #         api_data = call_data.json()
    #         return api_data
        
    #     else:

    #         try:
    #             api_data = call_data.json()
    #             logger.error(api_data['description'])
    #             return False
            
    #         except ValueError as error:
    #             logger.error(error)
    #             time.sleep(1)
    #             return get_api_call_data(url)
            
    #         except Exception as error:
    #             logger.error(error)
    #             return get_api_call_data(url)


def inch_swap(privatekey, retry=0, first = False, last = False):
        
    try:

        logger.info('1inch_swap')

        inch_version = 5

        rows = value_1inch_swap(first, last, privatekey)
        for row in rows:
            [chain, amount_from, amount_to, from_token_address, to_token_address, slippage, from_symbol, to_symbol] = row

            divider = 1

            web3 = Web3(Web3.HTTPProvider(DATA[chain]['rpc']))
            chain_id = web3.eth.chain_id

            if from_token_address == '': 
                from_token_address = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
                from_decimals = 18
                from_symbol = DATA[chain]['token']
            else:
                from_token_contract, from_decimals, from_symbol = check_data_token_chain(chain, from_token_address)

            if to_token_address   == '': 
                to_token_address   = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
                to_symbol = DATA[chain]['token']

            else:
                to_token_contract, to_decimals, to_symbol = check_data_token_chain(chain, to_token_address)

            account = web3.eth.account.from_key(privatekey)
            wallet  = account.address

            amount = round(random.uniform(amount_from, amount_to), 8)
            amount = amount*0.999
            amount_to_swap = intToDecimal(amount, from_decimals) 

            logger.info(f'{chain} : {amount} {from_symbol} => {to_symbol}')

            spender_json    = get_api_call_data(f'https://api.1inch.io/v{inch_version}.0/{chain_id}/approve/spender')
            spender         = Web3.to_checksum_address(spender_json['address'])

            # если токен не нативный, тогда проверяем апрув и если он меньше нужного, делаем апруваем
            if from_token_address != '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE':
                sleeping(8, 12)
                approve_(amount_to_swap, privatekey, chain, from_token_address, spender)

            _1inchurl = f'https://api.1inch.io/v{inch_version}.0/{chain_id}/swap?fromTokenAddress={from_token_address}&toTokenAddress={to_token_address}&amount={amount_to_swap}&fromAddress={wallet}&slippage={slippage}'
            json_data = get_api_call_data(_1inchurl)



            if json_data == False: 
                
                logger.info('failed to swap in 1inch')

            else:

                # cprint(json_data, 'yellow')

                tx  = json_data['tx']

                tx['chainId']   = chain_id
                tx['nonce']     = web3.eth.get_transaction_count(wallet)
                tx['to']        = Web3.to_checksum_address(tx['to'])
                tx['gasPrice']  = int(tx['gasPrice'])
                tx['gas']       = int(int(tx['gas']) / divider)
                tx['value']     = int(tx['value'])

                # cprint(tx, 'blue')

                if chain == 'bsc':
                    tx['gasPrice'] = random.randint(1000000000, 1050000000) # специально ставим 1 гвей, так транза будет дешевле


                        
                tx_hash     = sign_tx(web3, tx, privatekey)
                tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                module_str = f'1inch_swap : {round_to(amount)} {from_symbol} => {to_symbol}'

                status  = check_status_tx(chain, tx_hash)

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')
                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        logger.info(f'try again in 10 sec.')
                        sleeping(10, 10)
                        inch_swap(privatekey, retry+1)

            sleeping (40, 80)
        
    except KeyError:
        logger.error(json_data['description'])
        module_str = f'1inch_swap'
        list_send.append(f'{STR_CANCEL}{module_str}')

    except Exception as error:
        module_str = f'1inch_swap'
        logger.error(f'{module_str} | error : {error}')
        if retry < RETRY:
            logger.info(f'try again in 10 sec.')
            sleeping(10, 10)
            inch_swap(privatekey, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')
