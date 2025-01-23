#####################################
#
# If you meet 429 when running this script, please increase the `GLOBAL_API_RATE_LIMIT` in your Chat-API service.
# See more details in https://github.com/ai365vip/chat-api?tab=readme-ov-file#%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F
#
#####################################

import argparse
import concurrent.futures

from oneapi_manager import OneAPIManager
from cursor import Cursor

def handle_oneapi_cursor_channel(oneapi: OneAPIManager,
                                 channel_id,
                                 test_channel: bool,
                                 disable_low_balance_channel: bool, 
                                 delete_low_balance_channel: bool,
                                 low_balance_threshold = 10):
    if test_channel:
        test_response = oneapi.test_channel(channel_id)
        if test_response.status_code != 200:
            print(f"Fail to test channel {channel_id}. Status Code: {response.status_code}")
            return None

    response = oneapi.get_channel(channel_id)
    if response.status_code != 200:
        print(f"Fail to get channel {channel_id}. Status Code: {response.status_code}")
        return None

    data = response.json()['data']
    key = data['key']
    status = data['status'] # 1 for enable, 2 for disbale
    test_time = data['test_time']
    response_time = data['response_time']
    remaining_balance = Cursor.get_remaining_balance(key)
    remaining_days = Cursor.get_trial_remaining_days(key)
    print(f"[OneAPI] Channel {channel_id} Info: Balance = {remaining_balance}. Trial Remaining Days = {remaining_days}. Response Time = {response_time}")

    if None in [remaining_balance, remaining_days]:
        print(f"[OneAPI] Invalid resposne")
        return None

    if remaining_balance < low_balance_threshold \
        or (test_time != 0 and response_time < 1000): # or remaining_days <= 0:
        if delete_low_balance_channel:
            response = oneapi.delete_channel(channel_id)
            print(f"[OneAPI] Delete Channel {channel_id}. Status Coue: {response.status_code}")
        elif disable_low_balance_channel and status == 1:
            response = oneapi.disable_channel(channel_id)
            print(f"[OneAPI] Disable Channel {channel_id}. Status Code: {response.status_code}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--oneapi_url', type=str, required=False, help='URL link for One-API website')
    parser.add_argument('--oneapi_token', type=str, required=False, help='Token for One-API website')
    parser.add_argument('--test_channel', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--disable_low_balance_accounts', default=False, type=lambda x: (str(x).lower() == 'true'))
    parser.add_argument('--delete_low_balance_accounts', default=False, type=lambda x: (str(x).lower() == 'true'))

    parser.add_argument('--max_workers', type=int, default=10, help="How many workers in multi-threading")

    args = parser.parse_args()
    oneapi_url = args.oneapi_url
    oneapi_token = args.oneapi_token
    test_channel = args.test_channel
    disable_low_balance_accounts = args.disable_low_balance_accounts 
    delete_low_balance_accounts = args.delete_low_balance_accounts
    max_workers = args.max_workers

    oneapi = OneAPIManager(oneapi_url, oneapi_token)

    response_channels = oneapi.get_channels(0, 2147483647)
    channels = response_channels.json()['data']
    channels_ids = [channel['id'] for channel in channels]
    channels_ids = sorted(channels_ids, key=int)
    print(f"[OneAPI] Channel Count: {len(channels_ids)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(handle_oneapi_cursor_channel, 
                                   oneapi, id, test_channel, disable_low_balance_accounts, delete_low_balance_accounts) 
                                   for id in channels_ids]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
