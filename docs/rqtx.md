# rqtx 的 32 字节计算

`clientsdk/rqtx.Sum32(input [32]byte) uint32` 计算原 `v08.dll` 导出函数 `rqtx` 对固定 32 字节输入的结果。调用方应先把输入准备为**恰好 32 字节**；返回值是 `uint32`。该接口不读取 `rqtx.dat`，不加载 DLL，也不使用 cgo 或 `unsafe`。接口采用值参数，可以并发调用。

```go
var input [32]byte
copy(input[:], []byte("00000000000000000000000000000000"))
result := rqtx.Sum32(input) // 0x440b4622
```

这个结果不是标准 SHA-256、HMAC-SHA256 或 MD5。固定参数取自本仓库所带 `rqtx.dat`；这些名称只描述结构，不能用标准库中的同名散列函数直接替换。原导出函数的已核对路径读取 32 字节输入；这里不承诺其他长度的兼容行为。

现有 `v08.Rqtx(md5 string)` 保留原签名，按字节取字符串前 32 字节交给 `Sum32`；少于 32 字节返回 `0`，以避免原动态库路径可能发生的越界读取。Windows 上沿用旧 `dynlib.Call` 的字符串转换语义：整条字符串任意位置含 NUL 字节都返回 `0`，即使 NUL 位于前 32 字节之外。非 Windows 平台仍只用前 32 字节计算。纯计算接口 `Sum32([32]byte)` 接受任意 32 字节，包括 NUL。这里的“32 字节”不是 32 个 Unicode 字符。若传入的是 MD5 表示形式，需使用 32 字节 ASCII 十六进制文本，而不是 16 字节原始摘要。这个短输入处理是 Go 包装层新增的安全语义，不代表已证明原 DLL 对短输入返回 `0`。

## 算法结构

所有字运算均以 `uint32` 模 `2^32`，`RR(x,n)` 表示 32 位循环右移。固定 64 字节 `key`、初始状态与轮常量见 [`constants.go`](../clientsdk/rqtx/constants.go)。两个 256 位变体阶段分别计算 `hash((key XOR 0xec) || input)` 和 `hash((key XOR 0xdf) || innerDigest)`；每次先压缩一个 64 字节 key 块，再压缩一个包含 32 字节输入或内层摘要的尾块，总消息长度均为 96 字节。尾块追加 `0xfc`，补零到偏移 56，尾 8 字节写入大端 `~(96*8)`。结果为八个状态字的大端串接。

256 位压缩的每四个块字节 `(b0,b1,b2,b3)` 组成 `b0<<24 | b3<<16 | b2<<8 | b1`。消息扩展为 `W[i]=W[i-16]+W[i-7]+s0(W[i-15])+s1(W[i-2])`，其中 `s0(x)=RR(x,3) XOR RR(x,11) XOR (x>>5)`，`s1(x)=RR(x,5) XOR RR(x,9) XOR (x>>2)`。64 轮中，`T1=h+W[i]+K[i]+(RR(e,7) XOR RR(e,13) XOR RR(e,17))+((e&f)|(~e&g))`，`T2=(RR(a,5) XOR RR(a,11) XOR RR(a,19))+(((b XOR c)&a) XOR (b&c))`；工作状态按 `(a,b,c,d,e,f,g,h)=(T1+T2,a,b,c,d+T1,e,f,g)` 更新。轮后按**反序**将 `(h,g,f,e,d,c,b,a)` 加回八个状态字。有效轮常量 `K[i]` 已固化在 `constants.go`，它在原数据中的选择规则为 `i%3==0` 取第一张表，否则取第二张表。

随后将 32 字节外层摘要送入 128 位变体。尾块追加 `0xda`，补零至偏移 56，尾 8 字节写入小端 `(32*8) XOR 0x64130efb`。每四个字节组成 `M[j]=b2 | b1<<8 | b0<<16 | b3<<24`。64 轮令 `t=a+F(b,c,d)+K[i]+M[g]`，然后 `(a,b,c,d)=(d,b+RR(t,s),b,c)`；各段的 `F`、`g` 与循环移位 `s` 如下：

| 轮次 `i` | `F(b,c,d)` | `g` | 循环移位 `s` |
| --- | --- | --- | --- |
| 0–15 | `b XOR c XOR d` | `i` | 7, 12, 17, 22 |
| 16–31 | `(b&d) | (c&~b)` | `(5i+1)%16` | 5, 9, 14, 20 |
| 32–47 | `(b&~d) | (c&d)` | `(3i+5)%16` | 4, 11, 16, 23 |
| 48–63 | `c XOR (d|~b)` | `(7i)%16` | 6, 10, 15, 21 |

尾块压缩后，将 `(d,b,c,a)` 而非 `(a,b,c,d)` 加回四个初始状态字，按小端串接为 16 字节 `digest`。对 `digest[0:14]`、`digest[1:15]`、`digest[2:16]` 各自从零开始逐字节折叠 `p=133*p+byte`，只保留低 8 位，得到 `p0,p1,p2`。最终值为 `0x44000000 | ((p2 & 0x7b)<<16) | ((p1 & 0x6f)<<8) | (p0 & 0x3f)`，因此最高字节固定为 `0x44`。

## 验证依据和边界

[`clientsdk/rqtx/testdata/oracle-vectors.json`](../clientsdk/rqtx/testdata/oracle-vectors.json) 包含 327 条固定输入与预期结果：7 条边界样本、64 条单比特样本、128 条 ASCII MD5 文本和 128 条任意 32 字节样本。JSON 保留了生成方法、随机种子以及来源文件的 SHA-256；测试逐条核对全部结果，并检查重复调用和并发调用。单样本 `"0"` 重复 32 次的中间状态也已在分析记录中与机器码快照对照：内层摘要 `95a1b5297441e34625daa168774eaed439afaac36d003be80f7c10514dcff5e3`，外层摘要 `5aabd745ba1ed939ef772cb156be661314bc294c8fb74881a707212c4e59d24b`，MD5 式阶段输出 `b5d1e1b47d57afceeebb5c58b6eb99e6`，最终结果 `0x440b4622`。中间状态核验属于分析证据，公开 API 测试只核对最终输出。

预期结果来自 Unicorn 2.1.4 执行原 Windows x86-64 `rqtx` 与 VM 的机器码。loader 初始化按原伪代码重建，只 stub 了 `memset`；这**不是** Windows 原生进程中的完整 DLL、CRT、文件生命周期或微信端到端测试。来源文件 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `v08.dll` | `aeab62515c77dcb3e56ce6180a5635d1c16ecd747f9f9b6366b2005544a3f756` |
| `rqtx.dat` | `57def9708a23be4992fc0024754da9eaa8179651d210a3fe5e72cf3d9cdd2c6d` |

仓库中 Linux x86-64 `lib/libv08.so` 的计算核心也通过了相同的 **327/327** 样本对照（SHA-256 `c89374360a439abb24bf551eda04c3001fda4b58a2bf33d9e610222382796ddf`）。Linux 模拟按其 SysV ABI、GOT 和 TLS 配置，重建原初始化中的单节点范围树，执行原 SO 的包装、VM 和范围查询 helper 机器码；仍只 stub `memset`，并验证完整执行块处于白名单范围。它证明已列样本的跨库计算一致性，不代表原生 Linux 动态链接、文件初始化或完整服务生命周期已验收。

在仓库根目录运行：

```sh
CGO_ENABLED=0 go test ./clientsdk/rqtx
# 仅加载纯 Go 包装文件，避开 v08 包既有的原生库 init
CGO_ENABLED=0 go test clientsdk/v08/rqtx.go clientsdk/v08/rqtx_test.go
```

如需检查并发访问，可在支持 race 检测器的环境中另行运行 `go test -race ./clientsdk/rqtx`。这些测试证明已列样本的数值一致性，不能据此推断微信登录已验收。

要从固定来源重新生成 oracle 向量，可在仓库根目录创建独立 Python 环境并运行：

```sh
python3 -m venv /tmp/rqtx-oracle-venv
/tmp/rqtx-oracle-venv/bin/python -m pip install -r tools/rqtx/requirements.txt
/tmp/rqtx-oracle-venv/bin/python tools/rqtx/oracle.py --output /tmp/rqtx-oracle-vectors.json
```

单例可用 `--input-hex` 传入 64 位十六进制字符串，例如 `3030303030303030303030303030303030303030303030303030303030303030`。脚本执行前会核对本仓库 `v08.dll` 和 `rqtx.dat` 的 SHA-256，不匹配即拒绝执行；每例设置时间与指令预算。全量再生需要逐例模拟机器码，生成文件位于给定输出路径，不会自动覆盖仓库内的测试向量。重新生成后应按 `input_hex` 和 `output` 对比 327 条记录及来源元数据。

Linux 计算核心可用同一环境复核已有向量：

```sh
/tmp/rqtx-oracle-venv/bin/python tools/rqtx/oracle_linux.py --output /tmp/rqtx-linux-results.json
```

该脚本固定 SO/dat 的来源身份，逐例核对向量；不一致时以非零状态退出并保留报告。可先增加 `--limit 7` 验证边界样本。单进程完整模拟可能需要数分钟至十余分钟，应确认报告中的 `count`、`passed` 都为327。

`clientsdk/v08` 的其他 `EncodeString`、`EncodeUInt64` 等调用仍依赖原动态库；替换 `Rqtx` 的计算不代表整个项目或 `v08` 包已成为纯 Go。
