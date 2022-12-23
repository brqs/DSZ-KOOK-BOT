# dsz-kook-bot

<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt=""/>

一个基于 [khl.py](https://github.com/TWT233/khl.py)的[xiaomai-bot: 战地1寄气人 (github.com)](https://github.com/g1331/xiaomai-bot)的kook移植版。

加入**ddf**kook服务器查看具体功能演示邀请链接https://kook.top/HRNCP2

## 功能简览:

- 目前支持的主要服务：
  - bf1战绩查询:
    - 查询武器、载具、生涯数据
    - 查询最近游玩的数据、对局数据
    - 查询被封禁、vip、管理服务器、拥有服务器、vban数
    - 查询战绩查询软件被标记外挂、嫌疑数
  - bf1服务器管理：
    - 玩家操作：踢出、封禁、换边、vip操作
    - 服务器换图、重开、获取玩家列表

## 简易搭建:

1. python3.10+环境

2. 在bot根目录下使用

   ```
   pip install -r requirements.txt
   ```

   安装requirements里的依赖(或者其他你喜欢的方式,推荐使用虚拟环境)

3. 在config文件夹内的config文件填写配置信息

4. 点击bot.py运行

~~5.根据报错缺啥弄啥吧(~~

## 战地一查询配置默认账号:

- 在config文件夹内的config文件填写bf1查询默认账号的pid

- 从ea网站cookie中获取你查询账号的cookie信息:remid和sid

  - 然后在data/battlefield/managerAccount/账号pid/account.json中填入以下信息:

    ```
    {
     "remid":"你的remid",
     "sid":"你的sid"
    }
    ```

- 在config文件夹内的config文件填写你拥有的服务器信息gid，sid，guid

## kook开发者token

在kook开发者中心获取的token填入bot.py中

