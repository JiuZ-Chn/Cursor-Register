<p align="center">
  <span>
   <a href="https://github.com/JiuZ-Chn/CursorRegister/blob/main/README.md">English</a>  | 
   <a href="https://github.com/JiuZ-Chn/CursorRegister/blob/main/README.zh_CN.md">简体中文</a>
  </span>
<p>

# Cursor 注册机

自动注册Cursor账号并保存邮箱、密码和令牌(token)

大陆的网络环境可能对本项目性能有较大影响，如果注册成功率较低，请考虑使用代理或者使用其他网络。此外本项目提供Github Action以供网络条件不便的用户试用。

## 功能

- 注册Cursor账号并保存账号、密码、令牌(token)到本地
- 注册Cursor账号并上传令牌(token)到Chat-API
- 管理Chat-API中额度不足的Cursor账号（支持删除/禁用）
- 上述功能均支持在Github Action中运行

## 本地运行

### 安装依赖 **(务必使用 `Python >= 3.10`)**

```
pip install -r requirements.txt
```

### 注册账号，并将账号信息保存到csv文件

```
python cursor_register.py register.number=3
```
- `number`: 希望注册的账号数量

### 注册账号，并将账号的令牌(Cookie token)导入到[Chat-API](https://github.com/ai365vip/chat-api)

```
python cursor_register.py oneapi.url={oneapi_url} oneapi.token={oneapi_token} oneapi.channel_url={oneapi_channel_url} oneapi.enabled=true register.number=5
```
- `oneapi_url`: Chat-API 地址
- `oneapi_token`: Chat-API 访问令牌(token)，详见 [OneAPI API](https://github.com/songquanpeng/one-api/blob/main/docs/API.md)
- `oneapi_channel_url`: Cursor-API 反代服务地址，需自行搭建Cursor-API反代服务 [Cursor-To-OpenAI](https://github.com/JiuZ-Chn/Cursor-To-OpenAI)

### 管理[Chat-API](https://github.com/ai365vip/chat-api)的低额度渠道 

- [ChatAPI] 如果运行过程中出现429报错，需提高GLOBAL_API_RATE_LIMIT值，详见[ChatAPI环境变量](https://github.com/ai365vip/chat-api?tab=readme-ov-file#%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F)

```
python tokenManager/oneapi_cursor_cleaner.py --oneapi_url {oneapi_url} --oneapi_token {oneapi_token} --disable_low_balance_accounts {disable_low_balance_accounts} --delete_low_balance_accounts {delete_low_balance_accounts}
```
- `oneapi_url`: Chat-API 地址
- `oneapi_token`: Chat-API 访问令牌(token)，详见 [OneAPI API](https://github.com/songquanpeng/one-api/blob/main/docs/API.md)
- `disable_low_balance_accounts`: `True` 或 `False`，禁用Chat-API中的低额度账号
- `delete_low_balance_accounts`: `True` 或 `False`，删除Chat-API中的低额度账号

## 在Github Action中运行

GitHub Action适用于不便在本地搭建环境或本地环境不佳的用户以供试用。

### 注册账号，随后从[工作流程构件(GitHub Artifacts)](https://docs.github.com/zh/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/downloading-workflow-artifacts)中下载账号信息

适用于手动导入账户令牌(token)或Chat-API没有公网ip的用户。账号注册完成后需手动从工作流程构件(GitHub Artifacts)中下载账号信息。

**务必在下载完成后删除网页中的工作流程构件(GitHub Artifacts)以避免数据泄漏**

请运行 **`Cursor Register`** 并使用下列参数
- `number`: 希望注册的账号数量
- `max_workers`: 线程池的并行度. 推荐在Github Action中使用 `max_workers=1`
- `Ingest account tokens to OneAPI`: 不选此项，因为在此不必使用Chat-API服务
- `Upload account infos to artifact`: 选中此项，以保证数据被上传到工作流程构件(GitHub Artifacts)
 
### 注册账号，并将账号令牌(Cookie Token)直接导入到Chat-API](https://github.com/ai365vip/chat-api)

为了在GitHub Action中使用Chat-API服务，你需要在你的仓库中添加如下机密(secrets)，请参考 [Github 安全指南 - 为存储库创建机密](https://docs.github.com/zh/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository)

- `CURSOR_ONEAPI_URL`: 对应参数 `oneapi_url`
- `CURSOR_ONEAPI_TOKEN`: 对应参数 `oneapi_token`
- `CURSOR_CHANNEL_URL`: 对应参数 `oneapi_channel_url`

请运行 **`Cursor Register`** 并使用下列参数
- `number`: 希望注册的账号数量
- `max_workers`: 线程池的并行度. 推荐在Github Action中使用 `max_workers=1`
- `Ingest account tokens to OneAPI`: 选中此项，以开启Chat-API服务
- `Upload account infos to artifact`: 如果选中，那么数据也将被上传到工作流程构件(GitHub Artifacts)，如果不选则跳过该步骤。
 
### 管理[Chat-API](https://github.com/ai365vip/chat-api)中额度不足的Cursor账号 

请运行 **`OneAPI Cursor Cleaner`**。需要先保证已添加了下列机密(secrets)。

- `CURSOR_ONEAPI_URL`: 对应参数 `oneapi_url`
- `CURSOR_ONEAPI_TOKEN`: 对应参数 `oneapi_token`

参数：
- `Disable Low Balance Accounts`: 是否禁用额度较低的渠道
- `Delete Low Balance Accounts`: 是否删除额度较低的渠道

## 计划
- 修复多线程模式下可能存在的某些bugs。（众所周知多线程很容易出问题）
- 一个自动维护One-API中额度的Github Action pipeline

## 致谢
- 感谢[cursor-api](https://github.com/Old-Camel/cursor-api/)中的注册机代码思路
