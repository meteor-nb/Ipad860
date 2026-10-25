# Wechat860版本协议及源码——支持五端扫码登录

> 微信GO语言协议实现，支持长连接、RabbitMQ消息推送、五端扫码登录、文件上传并能使用几乎所有的微信功能。

## 协议支持登录客户端类型:

- ipad微信
- 安卓pad微信
- 车机版微信
- Windows PC微信
- Mac PC微信

## 下载:
去releases里面下载带二进制文件的版本

二进制文件安全性未知(虽然杀毒没发现异常),但是建议长期使用还是自己编译一下

zlib.dll是开源的,可以直接从github下载源代码编译

已还原 `v08.dll` 的 `rqtx` 固定 32 字节计算路径，并提供纯 Go 实现；算法、测试依据及验证边界见 [rqtx 说明](docs/rqtx.md)。`v08` 的其他导出调用仍依赖动态库。

---

## 使用:

解压，然后先启动redis文件夹里的redis-server.exe，最后运行main.exe，访问127.0.0.1:8058打开swagger UI

截至目前协议是可以用的而且没有封号，**但是注意如果登录选择的是PC微信,不可以使用PC微信没有的功能,比如发红包,检测好友关系,改个人信息等,不然秒封**

---

功能比较长,放最后了


## 功能:

---

## 1. 登录模块 (Login)

提供多种登录方式，支持二次登录、唤醒、62数据登录等。

### 功能列表：
- **`/Login/A16Data`**：A16登录(账号或密码)
- **`/Login/A16Data1`**：A16登录(账号或密码) - android == 新版云函数
- **`/Login/AutoHeartBeat`**：开启自动心跳, 自动二次登录, 自动推送消息(长链接)
- **`/Login/AutoHeartBeatLog`**：自动心跳日志
- **`/Login/CloseAutoHeartBeat`**：关闭自动心跳、自动二次登录
- **`/Login/Data62Login`**：62登录(账号或密码)
- **`/Login/Data62QRCodeApply`**：62登录(账号或密码), 并申请使用二维码验证
- **`/Login/Data62QRCodeVerify`**：62登录(账号或密码), 二维码验证校验
- **`/Login/Data62SMSAgain`**：62登录(账号或密码), 重发验证码
- **`/Login/Data62SMSApply`**：62登录(账号或密码), 并申请使用SMS验证
- **`/Login/Data62SMSVerify`**：62登录(账号或密码), 短信验证
- **`/Login/ExtDeviceLoginConfirmGet`**：新设备扫码登录
- **`/Login/ExtDeviceLoginConfirmOk`**：新设备扫码确认登录
- **`/Login/Get62Data`**：获取62数据
- **`/Login/GetA16Data`**：获取A16数据
- **`/Login/GetCacheInfo`**：获取登录缓存信息
- **`/Login/HeartBeat`**：心跳包
- **`/Login/HeartBeatLong`**：心跳包（长连接）
- **`/Login/LogOut`**：退出登录
- **`/Login/LoginAwaken`**：唤醒登录(只限扫码登录)
- **`/Login/LoginCheckQR`**：检测二维码
- **`/Login/LoginGetQR`**：获取二维码(iPad) --8.0.60
- **`/Login/LoginGetQRCar`**：获取二维码(Car)
- **`/Login/LoginGetQRMac`**：获取二维码(Mac)
- **`/Login/LoginGetQRPad`**：获取二维码(安卓Pad) --8.0.60
- **`/Login/LoginGetQRPadx`**：获取二维码(安卓Pad-绕过验证码)
- **`/Login/LoginGetQRWin`**：获取二维码(Windows)
- **`/Login/LoginGetQRWinUnified`**：获取二维码(WinUnified-统一PC版)
- **`/Login/LoginGetQRWinUwp`**：获取二维码(WindowsUwp-绕过验证码)
- **`/Login/LoginGetQRx`**：获取二维码(iPad-绕过验证码)
- **`/Login/LoginTwiceAutoAuth`**：二次登录
- **`/Login/Newinit`**：初始化
- **`/Login/YPayVerificationcode`**：提交登录验证码

---

## 2. 消息模块 (Msg)

支持发送各类消息，包括文本、图片、语音、视频、位置、名片、XML等。

### 功能列表：
- **`/Msg/Revoke`**：撤回消息
- **`/Msg/SendApp`**：发送App消息
- **`/Msg/SendCDNFile`**：发送文件(转发,并非上传)
- **`/Msg/SendCDNImg`**：发送Cdn图片(转发图片)
- **`/Msg/SendCDNVideo`**：发送Cdn视频(转发视频)
- **`/Msg/SendEmoji`**：发送Emoji
- **`/Msg/SendTxt`**：发送文本消息
- **`/Msg/SendVideo`**：发送视频
- **`/Msg/SendVoice`**：发送语音
- **`/Msg/ShareCard`**：分享名片
- **`/Msg/ShareLink`**：发送分享链接消息
- **`/Msg/ShareLocation`**：分享位置
- **`/Msg/ShareVideo`**：发送分享视频消息
- **`/Msg/Sync`**：同步消息
- **`/Msg/UploadImg`**：发送图片

---

## 3. 朋友模块 (Friend)

管理好友关系、黑名单、通讯录等。

### 功能列表：
- **`/Friend/Blacklist`**：添加/移除黑名单
- **`/Friend/Delete`**：删除好友
- **`/Friend/GetContractDetail`**：获取通讯录好友详情
- **`/Friend/GetContractList`**：获取通讯录好友
- **`/Friend/GetFriendstate`**：查询好友状态
- **`/Friend/GetMFriend`**：获取手机通讯录
- **`/Friend/LbsFind`**：附近人
- **`/Friend/PassVerify`**：通过好友请求
- **`/Friend/Search`**：搜索联系人
- **`/Friend/GetFriendRelation`**：好友关系检测 判断好友关系，1 删除 4自己拉黑 5被拉黑 0正常
- **`/Friend/SendRequest`**：添加联系人(发送好友请求)
- **`/Friend/SetRemarks`**：设置好友备注
- **`/Friend/Upload`**：上传通讯录

---

## 4. 视频号模块 (Finder)

管理视频号相关功能。

### 功能列表：
- **`/Finder/UserPrepare`** 用户中心

---

## 5. 朋友圈模块 (FriendCircle)

操作朋友圈内容，包括发布、点赞、评论、同步等。

### 功能列表：
- **`/FriendCircle/Comment`**：朋友圈点赞/评论
- **`/FriendCircle/GetDetail`**：获取特定人朋友圈
- **`/FriendCircle/GetIdDetail`**：获取特定ID详情内容
- **`/FriendCircle/DownFriendCircleMedia`**：下载朋友圈视频
- **`/FriendCircle/GetList`**：朋友圈首页列表
- **`/FriendCircle/Messages`**：发布朋友圈
- **`/FriendCircle/MmSnsSync`**：朋友圈同步
- **`/FriendCircle/Operation`**：朋友圈操作
- **`/FriendCircle/PrivacySettings`**：朋友圈权限设置
- **`/FriendCircle/Upload`**：朋友圈上传

---

## 6. 收藏模块 (Favor)

管理微信收藏内容。

### 功能列表：
- **`/Favor/Del`**：删除收藏
- **`/Favor/GetFavInfo`**：获取收藏信息
- **`/Favor/GetFavItem`**：读取收藏内容
- **`/Favor/Sync`**：同步收藏数据

---

## 7. 群组模块 (Group)

管理微信群，包括创建、邀请、踢人、管理员操作等。

### 功能列表：
- **`/Group/AddChatRoomMember`**：增加群成员(40人以内)
- **`/Group/ConsentToJoin`**：同意进入群聊
- **`/Group/CreateChatRoom`**：创建群聊
- **`/Group/DelChatRoomMember`**：删除群成员
- **`/Group/GetChatRoomInfo`**：获取群详情(不带公告内容)
- **`/Group/GetChatRoomInfoDetail`**：获取群信息(带公告内容)
- **`/Group/GetChatRoomMemberDetail`**：获取群成员详情
- **`/Group/GetQRCode`**：获取群二维码
- **`/Group/InviteChatRoomMember`**：邀请群成员(40人以上)
- **`/Group/MoveContractList`**：保存到通讯录
- **`/Group/OperateChatRoomAdmin`**：群管理操作(添加、删除、转让)
- **`/Group/Quit`**：退出群聊
- **`/Group/ScanIntoGroup`**：扫码进群
- **`/Group/ScanIntoGroupEnterprise`**：扫码进群
- **`/Group/SetChatRoomAnnouncement`**：设置群公告
- **`/Group/SetChatRoomName`**：设置群名称
- **`/Group/SetChatRoomRemarks`**：设置群备注(仅自己可见)

---

## 8. 标签模块 (Label)

管理好友标签。

### 功能列表：
- **`/Label/Add`**：创建标签
- **`/Label/Delete`**：删除标签
- **`/Label/GetList`** 获取标签列表
- **`/Label/UpdateList`**：更新标签列表
- **`/Label/UpdateName`**：修改标签

---

## 9. 用户模块 (User)

管理微信号个人信息、安全设置、绑定信息等。

### 功能列表：
- **`/User/BindQQ`**：绑定QQ
- **`/User/BindingEmail`**：绑定邮箱
- **`/User/BindingMobile`**：换绑手机号
- **`/User/DelSafetyInfo`**：删除登录设备
- **`/User/GetContractProfile`**：取个人信息
- **`/User/GetQRCode`**：取个人二维码
- **`/User/GetSafetyInfo`**：登录设备管理
- **`/User/PrivacySettings`**：隐私设置
- **`/User/ReportMotion`**：ReportMotion
- **`/User/SendVerifyMobile`**：发送手机验证码
- **`/User/SetAlisa`**：设置微信号
- **`/User/SetPasswd`**：修改密码
- **`/User/UpdateProfile`**：修改个人信息
- **`/User/UploadHeadImage`**：修改头像
- **`/User/VerifyPasswd`**：验证密码

---

## 10. 小程序模块 (Wxapp)

操作微信小程序，包括登录、授权、云函数调用等。

### 功能列表：
- **`/Wxapp/AddAvatar`**：AddAvatar
- **`/Wxapp/AddMobile`**：小程序绑定增加手机号
- **`/Wxapp/AddWxAppRecord`**：新增小程序记录
- **`/Wxapp/CloudCallFunction`**：小程序云函数
- **`/Wxapp/DelMobile`**：小程序删除手机号
- **`/Wxapp/GetAllMobile`**：GetAllMobile
- **`/Wxapp/GetRandomAvatar`**：GetRandomAvatar
- **`/Wxapp/GetUserOpenId`**：GetUserOpenId
- **`/Wxapp/JSGetSessionid`**：获取小程序支付sessionid
- **`/Wxapp/JSGetSessionidQRcode`**：获取付小程序款二维码
- **`/Wxapp/JSLogin`**：授权小程序(返回授权后的code)
- **`/Wxapp/JSOperateWxData`**：小程序操作
- **`/Wxapp/QrcodeAuthLogin`**：扫码授权登录app或网页
- **`/Wxapp/UploadAvatarImg`**：UploadAvatarImg

---

## 11. 企业联系人模块 (QWContact)

管理企业微信联系人。

额，暂时没找到接口文档，大家自己试试吧

---

## 12. 公众号模块 (OfficialAccounts)

操作公众号，如授权、获取Key、取消关注等。

### 功能列表：
- **`/OfficialAccounts/Follow`**：关注
- **`/OfficialAccounts/GetAppMsgExt`**：阅读文章,返回 分享、看一看、阅读数据
- **`/OfficialAccounts/GetAppMsgExtLike`**：点赞文章,返回 分享、看一看、阅读数据
- **`/OfficialAccounts/JSAPIPreVerify`**：JSAPIPreVerify
- **`/OfficialAccounts/MpGetA8Key`**：MpGetA8Key(获取文章key和uin)
- **`/OfficialAccounts/OauthAuthorize`**：OauthAuthorize
- **`/OfficialAccounts/Quit`**：取消关注

---

## 13. 打招呼模块 (SayHello)

用于主动添加好友时的打招呼功能。

### 功能列表：
- **`/SayHello/Modelv1`**：模式1-扫码
- **`/SayHello/Modelv2`**：模式3-v3\v4打招呼

---

## 14. 工具箱模块 (Tools)

提供各类辅助工具功能。

### 功能列表：
- **`/Tools/CdnDownloadImage`**：CDN下载高清图片
- **`/Tools/DownloadFile`**：文件下载
- **`/Tools/DownloadImg`**：高清图片下载
- **`/Tools/DownloadVideo`**：视频下载
- **`/Tools/DownloadVoice`**：语音下载
- **`/Tools/GeneratePayQCode`**：生成支付二维码
- **`/Tools/GetA8Key`**：GetA8Key
- **`/Tools/GetBandCardList`**：获取余额以及银行卡信息 **不可滥用此功能！！**
- **`/Tools/GetBoundHardDevices`**：GetBoundHardDevices
- **`/Tools/GetCdnDns`**：获取CDN服务器dns信息
- **`/Tools/OauthSdkApp`**：OauthSdkApp
- **`/Tools/ThirdAppGrant`**：第三方APP授权
- **`/Tools/UpdateStepNumberApi`**：修改微信步数
- **`/Tools/setproxy`**：设置/删除代理IP
- **`/Tools/UploadAppAttachApi`**：文件上传

---

## 14. 微信支付模块 (Tenpay)

自动使用微信支付功能, 部分功能需要支付密码。**不可滥用此模块！！否则可能导致账号封禁或者需要承担法律责任**

### 功能列表：
- **`/TenPay/Collectmoney`**：确认收款
- **`/TenPay/GeMaPayQCode`**：自定义个人收款二维码
- **`/TenPay/GeMaSkdPayQCode`**：自定义经营个人收款单
- **`/TenPay/GetEncryptInfo`**：获取加密信息
- **`/TenPay/AutoHongBao`**：抢红包
- **`/TenPay/Openwxhb`**：拆开红包
- **`/TenPay/Qrydetailwxhb`**：查看红包
- **`/TenPay/Receivewxhb`**：打开红包
- **`/TenPay/SjSkdPayQCode`**：自定义商家收款单
