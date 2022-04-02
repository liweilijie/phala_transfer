# pip install substrate-interface
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
import csv


if __name__ == '__main__':
    # connect rpc
    try:
        substrate = SubstrateInterface(
            url="ws://127.0.0.1:9944",
            ss58_format=30,
            # type_registry_preset='development'
        )
    except ConnectionRefusedError:
        print("⚠️ No local Substrate node running, try running 'start_local_substrate_node.sh' first")
        exit()


    dest = "43fagEW4hyAJwsNeGnHYMcWcsb1NZk49tcfuN1h7HcFN4yN6"

    # read csv
    with open('phala_gas.csv', newline='') as f:
        reader = csv.reader(f)
        data = list(reader)

    # 除了第一行,其他都用来转账
    for i in range(2, len(data)):
        print(data[i][0])
        seed = data[i][0]
        keypair = Keypair.create_from_mnemonic(seed, ss58_format=30)

        print(keypair.ss58_address)

        account_info = substrate.query('System', 'Account', params=[keypair.ss58_address])


        print('Account info free balance:', account_info["data"]["free"])

        balance = account_info["data"]["free"]
        #  手续费用
        gas_limit=2290000000

        # 发送交易
        try:
            free = int(str(balance)) - gas_limit
        except:
            free = 0


        if free > 0:
            print('Free balance:', free)
        else:
            print('Not enough balance')
            continue


        call = substrate.compose_call(
            call_module='Balances',
            call_function='transfer',
            call_params={
                'dest': dest,
                'value': free
            }
        )

        #  获取 payment info
        payment_info = substrate.get_payment_info(call=call, keypair=keypair)

        print("Payment info: ", payment_info)

        extrinsic = substrate.create_signed_extrinsic(
            call=call,
            keypair=keypair,
            era={'period': 64}
        )


        try:
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

            print('Extrinsic "{}" included in block "{}"'.format(
                receipt.extrinsic_hash, receipt.block_hash
            ))

            if receipt.is_success:

                print('✅ Success, triggered events:')
                for event in receipt.triggered_events:
                    print(f'* {event.value}')

            else:
                print('⚠️ Extrinsic Failed: ', receipt.error_message)


        except SubstrateRequestException as e:
            print("Failed to send: {}=>{}".format(e), data[i][0])


