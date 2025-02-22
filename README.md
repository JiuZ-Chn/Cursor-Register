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

### Register accounts

```
python cursor_register.py register.number=3
```
- `register.number`: The account number you want to register

### Advanced configuration in `config/config.yaml`

The `config.yaml` describe all the parameter for the account register. If you want to do advanced configuration, like IMAP or Chat-API, please edit the .yaml file for the parameter.

#### Basic register configuration
```
register:
  number: 1
  max_workers: 1
```
- `register.number`: The account number you want to register
- `register.max_workers`: Max worker number in multi-threading

#### Temp email server configuration

Default setting to get email verification code from temp email server

```
register:
  temp_email_server:
    name: Minuteinboxcom
```
-`register.temp_email_server.name`: Which temp email you are using

#### IMAP email server configuration

When you use IMAP to revice the email verification code, you should edit the parameter for your IMAP account.

```
register:
  email_server: 
    name: imap_email_server
    use_custom_address: true
    custom_email_address:
    - email1@outlook.com
    - email2@outlook.com

  imap_email_server:
    imap_server: imap.qq.com
    imap_port: 993
    username: username
    password: password
```
- `register.email_server.name`: Should be `imap_email_server` when use IMAP receives the email
- `register.email_server.use_custom_address`: Should be `true` when use IMAP receives the email
- `register.email_server.custom_email_address`: Email address list
- `register.imap_email_server`: Your IMAP server configuration

#### Upload the account cookie token into [Chat-API](https://github.com/ai365vip/chat-api)

You need to pay attention to the `oneapi` section. Set the `enabled` to `true` and replace the value of `url`, `token`, `channel_url` for your website.
```
oneapi:
  enabled: true
  url: http://localhost:3000
  token: your_oneapi_token
  channel_url: http://localhost:3010
```
- `oneapi.enabled`: Should be `true` when upload data into Chat-API
- `oneapi.url`: The web address for your chatapi server. 
- `oneapi.token`: The access token for your chatapi website. See more details in [OneAPI API](https://github.com/songquanpeng/one-api/blob/main/docs/API.md)
- `oneapi.channel_url`: The cursor-api reverse proxy server like [Cursor-To-OpenAI](https://github.com/JiuZ-Chn/Cursor-To-OpenAI)

### Manage low balance Cursor channels in [Chat-API](https://github.com/ai365vip/chat-api)

```
python tokenManager/oneapi_cursor_cleaner.py --oneapi_url {oneapi_url} --oneapi_token {oneapi_token} --disable_low_balance_accounts {disable_low_balance_accounts} --delete_low_balance_accounts {delete_low_balance_accounts}
```
- `oneapi_url`: The web address for your chatapi server. 
- `oneapi_token`: The access token for your chatapi website. See more details in [OneAPI API](https://github.com/songquanpeng/one-api/blob/main/docs/API.md)
- `disable_low_balance_accounts`: `True` or `False` to disable the low balance accounts in Chat-API
- `delete_low_balance_accounts`: `True` or `False` to delete the low balance accounts in Chat-API

## Run in Github Action

## Introduction

The Github Action pipeline **`Cursor Register`** provides the following parameter:
- `number`: The account number you want to register.
- `max_workers`: Parallelism for threading pool. Suggest to use `1` in Github Action environment.
- `email_server`: Support `TempEmail`, `IMAP`. You need to set your IMAP account via secret in repo you choose `IMAP`.
- `Ingest account tokens to OneAPI`: Mark as `☑` to create channel Chat-API service. Mark as `☐` will skip this step. You need to set your IMAP account via secret in repo you choose to enable this.
- `Upload account infos to artifact`: Mark as `☑` to make Github Action uploead the csv files to artifacts. Then you can download them after workflow succeeds.  Mark as `☐` will skip this step.

If you are new to use secret in Github Action. you can add the secret following [Security Guides](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository) 

### Register accounts. Download account info and cookie token from Github Artifact.

If you want to use the token directly or your ChatAPI does not have a public IP, you can manually download `token.csv` after running the GitHub Action pipeline. **Do not forget to delete the artifact after you download it to avoid data leakage.**

Please run the Github Action pipeline **`Cursor Register`** with the following parameter:
- `Upload account infos to artifact`: Should be `☑`.

### Register accounts. Upload the account cookie token into [Chat-API](https://github.com/ai365vip/chat-api)

Please add the folloing secret in your repo.

- `CURSOR_ONEAPI_URL`: For parameter `oneapi.url`
- `CURSOR_ONEAPI_TOKEN`: For parameter `oneapi_.oken`
- `CURSOR_CHANNEL_URL`: For parameter `oneapi.channel_url`

Please run the Github Action pipeline **`Cursor Register`** with the following parameter:
- `Ingest account tokens to OneAPI`: Should be `☑`

### Register accounts. Use IMAP server to revice the email

Please add the folloing secret in your repo:

- `CURSOR_IMAP_SERVER`: IMAP server
- `CURSOR_IMAP_PORT`: IMAP port
- `CURSOR_IMAP_USERNAME`: IMAP username
- `CURSOR_IMAP_PASSWORD`: IMAP passowrd
- `CURSOR_CUSTOM_EMAIL_ADDRESS`: Email addresses, separated by commas

Please run the Github Action pipeline **`Cursor Register`** with the following parameter:
- `email_server`: Should be `IMAP`

### Manage low balance Cursor channels in [Chat-API](https://github.com/ai365vip/chat-api)

Before runnign the pipeline, you need to add the following secrets in your repo.

- `CURSOR_ONEAPI_URL`: For parameter `oneapi.url`
- `CURSOR_ONEAPI_TOKEN`: For parameter `oneapi.token`

Please run the Github Action pipeline **`OneAPI Cursor Cleaner`**.

- `Disable Low Balance Accounts`: Disable low balance accounts or not
- `Delete Low Balance Accounts`: Delete low balance accounts or not

## Todo
- Maybe some bugs when running in multiple threading mode (`max_workers` > 1), but not sure. :(
- A new Github Action pipeline to automatically maintain the minimum balance of Curosr accounts in ChatAPI, and automatically register if the balance is too low.

## Thanks
- [cursor-api](https://github.com/Old-Camel/cursor-api/) for Python code in auto register
