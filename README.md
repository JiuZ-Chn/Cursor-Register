<p align="center">
  <span>
   <a href="https://github.com/JiuZ-Chn/CursorRegister/blob/main/README.md">English</a>  | 
   <a href="https://github.com/JiuZ-Chn/CursorRegister/blob/main/README.zh_CN.md">简体中文</a>
  </span>
<p>

# Cursor Register

Automatically register a Cursor account and save the account name, password, and token.


## Feature

- Register Cursor accounts and save account, password and token to .csv locally.
- Register Cursor accounts upload tokens to Chat API.
- Manage Cursor channels with low balance in Chat API.
- The above features all support to run in Github Action environment.

## Run in local

### Install dependency **(It's required to use `Python >= 3.10`)**

```
pip install -r requirements.txt
```

### Register accounts. Save the account info and cookie token into csv.

```
python cursor_register.py register.number=3
```
- `number`: The account number you want to register

### Register accounts. Upload the account cookie token into [Chat-API](https://github.com/ai365vip/chat-api)

```
python cursor_register.py oneapi.url={oneapi_url} oneapi.token={oneapi_token} oneapi.channel_url={oneapi_channel_url} oneapi.enabled=true register.number=5
```
- `oneapi_url`: The web address for your chatapi server. 
- `oneapi_token`: The access token for your chatapi website. See more details in [OneAPI API](https://github.com/songquanpeng/one-api/blob/main/docs/API.md)
- `oneapi_channel_url`: The cursor-api reverse proxy server like [Cursor-To-OpenAI](https://github.com/JiuZ-Chn/Cursor-To-OpenAI)

### Manage low balance Cursor channels in [Chat-API](https://github.com/ai365vip/chat-api)

```
python tokenManager/oneapi_cursor_cleaner.py --oneapi_url {oneapi_url} --oneapi_token {oneapi_token} --disable_low_balance_accounts {disable_low_balance_accounts} --delete_low_balance_accounts {delete_low_balance_accounts}
```
- `oneapi_url`: The web address for your chatapi server. 
- `oneapi_token`: The access token for your chatapi website. See more details in [OneAPI API](https://github.com/songquanpeng/one-api/blob/main/docs/API.md)
- `disable_low_balance_accounts`: `True` or `False` to disable the low balance accounts in Chat-API
- `delete_low_balance_accounts`: `True` or `False` to delete the low balance accounts in Chat-API

## Run in Github Action

### Register accounts. Download account info and cookie token from Github Artifact.

If you want to use the token directly or your ChatAPI does not have a public IP, you can manually download `token.csv` after running the GitHub Action pipeline. **Do not forget to delete the artifact after you download it to avoid data leakage.**

Please run the Github Action pipeline **`Cursor Register`** with the following parameter:
- `number`: The account number you want to register.
- `max_workers`: Parallelism for threading pool. Suggest to use `1` in Github Action environment.
- `Ingest account tokens to OneAPI`: Mark as `☐` to disable Chat-API service.
- `Upload account infos to artifact`: Mark as `☑` to make Github Action uploead the csv files to artifacts. Then you can download them after workflow succeeds.

### Register accounts. Upload the account cookie token into [Chat-API](https://github.com/ai365vip/chat-api)

Before ingest the account cookie into Chat API, you need to add the following secret in your repo. If you are new to use secret in Github Action. you can add the secret following [Security Guides](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository) 

- `CURSOR_ONEAPI_URL`: For parameter `oneapi_url`
- `CURSOR_ONEAPI_TOKEN`: For parameter `oneapi_token`
- `CURSOR_CHANNEL_URL`: For parameter `oneapi_channel_url`

Please run the Github Action pipeline **`Cursor Register`** with the following parameter:
- `number`: The account number you want to register.
- `max_workers`: Parallelism for threading pool. Suggest to use `1` in Github Action environment.
- `Ingest account tokens to OneAPI`: Mark as `☑` to enable One-API service.
- `Upload account infos to artifact`: `☑` for uploeading the artifact and `☑` will skip this step

### Manage low balance Cursor channels in [Chat-API](https://github.com/ai365vip/chat-api)

Before runnign the pipeline, you need to add the following secrets in your repo.

- `CURSOR_ONEAPI_URL`: For parameter `oneapi_url`
- `CURSOR_ONEAPI_TOKEN`: For parameter `oneapi_token`

Please run the Github Action pipeline **`OneAPI Cursor Cleaner`**.

- `Disable Low Balance Accounts`: Disable low balance accounts or not
- `Delete Low Balance Accounts`: Delete low balance accounts or not

## Todo
- Maybe some bugs when running in multiple threading mode (`max_workers` > 1), but not sure. :(
- A new Github Action pipeline to automatically maintain the minimum balance of Curosr accounts in ChatAPI, and automatically register if the balance is too low.

## Thanks
- [cursor-api](https://github.com/Old-Camel/cursor-api/) for Python code in auto register
