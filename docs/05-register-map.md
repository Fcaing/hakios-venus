# 寄存器与结构速查（venus 实测值）

> 全部是**这台机器上读出来的值**，不是 datasheet 抄来的。读不到或不一致的地方都标了。
> 陷阱：`0x152128` 是 TZ 保护地址，**一读就 panic**。

---

## 1. SoC 级地址

| 名称 | 地址 | 说明 |
|---|---|---|
| PARF | `0x1c00000`（+0x3000） | PCIe 控制器配置 |
| PHY（QMP v5） | `0x1c06000`（+0x2000） | 75 条 vendor 序列 |
| DBI | `0x60000000` | 控制器自身配置空间 |
| ELBI（状态 `+0x08`，bit10 = LINK_UP） | `0x60000f20` | `link UP: ELBI 0x08 = 0x00011401` |
| ECAM（1 MiB） | `0x60100000` | 端点 `17cb:1103` |
| iATU | `0x60001000` | outbound 映射 |
| TLMM | `0xf100000`（`GPIO_CFG(n) = +0x1000*n`，`GPIO_IO = +4`，bit1 = 输出电平） | PERST# = 94、WLAN_EN = 64、CLKREQ = 95、BT_EN = 65、SW_CTRL = 153 |
| 命令库 | `0x80860000`（+0x20000） | `cmddb=2` 转储 4 slave / 161 条 |
| RSC / TCS | `0x18220000`（+0x10000），`tcs-offset 0xd00`，`drv-id 2` | RPMh 投票 |
| GCC 投票 page0 / page1 | `0x52000` / `0x52008`（mask `0x004c0c00` / `0x3f`） | `0x52000=0x00e0057f → 0x00ec0d7f` |
| GDSCR（`GCC_PCIE_0_GDSC`） | `0x6b004` | bit0 = SW_COLLAPSE、bit31 = PWR_ON；`0x0022f001 → 0xf822f000` |
| `gcc_pcie_0_clkref_en` | `0x8c004` bit0 | |

**PHY 关键位**

| 名称 | 地址 | 用法 |
|---|---|---|
| PARF LTSSM | `0x1b0` | **置位** bit8 启动训练（不要清零） |
| PHY PCS 状态 | `0x214` bit6 | **清零** = PLL 锁相成功 |
| PHY power-down / start | `0x240`（先写 3）/ `0x244`（bits 0\|1） | |

---

## 2. BAR0 内：MHI

| 偏移 | 名称 | venus 实测 |
|---|---|---|
| `0x00` / `0x04` | MHIREG / MHIVER | `0x00000100`；版本读出来是垃圾（`0xdeadbeef`），**别用** |
| `0x10` | MHICFG | `0x00030880` = NCH 128 / NHWCH 3 / NER 3 / NHWER 2 |
| `0x18` | CHDBOFF | `0x300`（通道门铃 `0x300 + ch*8`，ch20 → **`0x3a0`**） |
| `0x20` | ERDBOFF | `0x700`（事件门铃 `0x700 + er*8`） |
| `0x28` | BHIOFF | `0x100` |
| `0x2c` | BHIEOFF | `0x224` |
| `0x38` | MHICTRL | 状态在 bit8-15：M0 = `2<<8`、M2 = `4<<8`、BHI = `7<<8`、SYS_ERR = `0xff00`；RESET = bit1 |
| `0x48` | MHISTATUS | bit8-15 同上；bit0 READY、bit2 SYSERR。健康值 `0x201`（M0+READY） |
| `0x58/0x5c` | CCABAP_H/L | `0xa0200000` |
| `0x60/0x64` | ECABAP_H/L | `0xa0202000` |
| `0x68/0x6c` | CRCBAP_H/L | `0xa0202400` |
| `0x70/0x74` | CRDB | 命令门铃 |
| `0x80/0x84` | MHICTRLBASE | `0xa0000000` |
| `0x88/0x8c` | MHICTRLLIMIT | `0xb0000000` |
| `0x98/0x9c` | MHIDATABASE | `0xa0000000` |
| `0xa0/0xa4` | MHIDATALIMIT | `0xb0000000` |
| **`0xb0`** | `MHI_SOC_RESET_REQ` | 写 1 → 7–20 ms 进 `EE=3`；**再写一次可钉住** |
| `0x128` | EE | 0 PBL / 1 SBL / **2 AMSS** / 3 RDDM |
| `0x6f0` | BW scale DB | |
| `0x6f8` | wake DB | `CHDBOFF + 8*127` |
| `0x700 + er*8` | 事件门铃 | |

## 3. BAR0 内：BHI / BHIE

**BHI（`BHIOFF = 0x100` 处）**

| 偏移 | 名称 | 说明 |
|---|---|---|
| `0x00/0x04` | ver | |
| `0x08/0x0c` | IMGADDR_LOW/HIGH | `0xa0004000` |
| `0x10` | IMGSIZE | `0x80000`（写之前它已经是这个值；5 MB 镜像体积与此无关） |
| `0x18` | IMGTXDB | 门铃；vendor 用随机非零，写 1 也能工作 |
| `0x20` | INTVEC | |
| `0x28` | EXECENV | |
| `0x2c` | STATUS | top2：0 RESET / 2 SUCCESS / 3 ERROR；低 30 位 = 门铃序号回显。`0x80000001` = SUCCESS+READY |
| `0x30` | ERRCODE | |
| `0x34/0x38/0x3c` | ERRDBG1-3 | |
| `0x40` | SERIALNUM | |
| `0x48` | NUMSEG | |

**BHIE（`BHIEOFF = 0x224` 处）**

| 偏移 | 名称 |
|---|---|
| `0x2c/0x30` | TXVECADDR_LOW/HIGH |
| `0x34` | TXVECSIZE |
| `0x3c` | TXVECDB |
| `0x44` | TXVECSTATUS（`0xbbd056f0` = XFER_COMPL + seq） |
| `0x60/0x64` | RXVECADDR_LOW/HIGH |
| `0x68` | RXVECSIZE |
| `0x70` | RXVECDB |
| `0x78` | RXVECSTATUS |

向量 16 B / 条，512 KiB 一块。

---

## 4. 上下文与环（stride `0x2c`）

| 字段 | 偏移 | 通道 | 事件 | 命令 |
|---|---|---|---|---|
| word0 | `0x00` | `chstate:8 / brstmode:2 / pollcfg:6 / rsvd:16` | `rsvd:8 / intmodc:8 / intmodt:16` | — |
| | `0x04` | `chtype` | `ertype` | reserved |
| | `0x08` | `erindex`（**不是 ee**） | `msivec` | reserved |
| | `0x0c` | `rbase`（64 位） | 同 | 同 |
| | `0x14` | `rlen` | 同 | 同 |
| | `0x1c` | `rp` | 同 | 同 |
| | `0x24` | `wp` | 同 | 同 |

**位置**（相对 `pcie_dma_extra`）：

| 区 | 偏移 |
|---|---|
| 通道上下文 | `ch*0x2c`（ch20 → `0x370`，ch21 → `0x39c`）**没有 +0x2000** |
| 事件上下文 | `0x2000 + er*0x2c` |
| 命令上下文 | `0x2400` |
| 事件环 | `+0x4000`（er0）/ `+0x5000`（er1）/ `+0x6000`（er2） |
| 命令环 | `+0x7000` |
| 数据环 | `0x8000 + didx*0x1000`（didx 0..5 ↔ ch 0,1,4,5,20,21） |

`chstate`：0 = disabled、1 = ENABLED、2 = RUNNING；固件给的是 `0x0202`（RUNNING + brstmode 2）。

---

## 5. TRE（16 字节/条）

```
struct mhi_tre { u64 ptr; u32 dword0; u32 dword1; }
```

| 字段 | 含义 |
|---|---|
| `ptr` | payload 的 IOVA |
| `dword0` | 数据 TRE 不用；事件 TRE 里低字节 = 状态（1 = SUCCESS） |
| `dword1` | **数据 TRE**：`(2<<16) \| (bei<<10) \| (ieot<<9) \| (ieob<<8) \| chain` → 实测 `0x00020200` |
| | **事件 TRE**：bit16-23 = 类型，**低 8 位 = 通道号** |

事件类型：

| 值 | 类型 |
|---|---|
| `0x12` | START_CHAN |
| `0x20` | STATE_CHANGE |
| `0x21` | CMD_COMPLETION |
| `0x22` | TX_EVENT |
| `0x25` | BW_REQ_EVENT |
| `0x40` | EE_EVENT |
| `0x48` | TSYNC |

**门铃写法**：先写 `db+4`（高 32 位）再写 `db`（低 32 位），值 = 环的 wp IOVA。

---

## 6. 内存布局（我们这一侧）

| 区 | 地址 |
|---|---|
| MHI 窗 | `0xa0000000 .. 0xb0000000`（8 MB 起用） |
| `pcie_dma_extra` | `0xa0200000`（可整块搬家，`apply-354` 试过 `0xa1c00000`，结论：搬家不改变结果） |
| BHI 上传窗口 | `0xa0004000`（`pcie_bhi_addr`，`pcie_bhi_size=0x80000`） |
| 镜像副本 | `0xa0220000` 起 5 MB（结束约 `0xa071fa50`）——**RDDM 不能放这里面** |
| ch0 / ch1 环 | `0xa0208000` / `0xa0209000` |
| ch20 / ch21 环 | `0xa020c000` / `0xa020d000` |

真机（Android）对照：ctrl ≈ `0xa0100000`（命令环 `0xa0108000`）、data ≈ `0xa0c00000`、固件 staging `0xa0700000`。

---

## 7. 日常启动 cmdline（`boot_b`）

```
root_apfs=ufs_darwin ufs=2 ufs_native=1 ufs_write=1 var_hfs=ufs_darwin_data
adsp=1 pmic=1 bootcpu=7 cpus=8 cpufreq=1 touchscreen=1 buttons=1 gpu=1 gl=1
sb_delay=45 fbwidth=1440 fbheight=3200 debug=0x8
```

**`battery=1` 绝对不能加**，否则电池管理器不走 DSP、没有百分比。
loader 自己的前缀占 93 字符，**payload cmdline 只装得下 514**。

## 8. 测试 payload cmdline（Wi-Fi 探针全套）

```
pcie=1 pcie_step=5 pcie_power=1 pcie_delay=0 pcie_settle=100 pcie_bar=21 pcie_watch=0
pcie_star_mask=31 pcie_bhi_addr=0xa0004000 pcie_bhi_size=0x80000 pcie_novec=1 pcie_msi_test=1
pcie_mhi_nom0=1 pcie_chanstart=0 pcie_mhi_late0=1 pcie_mhi_data=NN pcie_starflow=1
```

`pcie_mhi_data` 决定跑哪一段探针；**它在 BHI 握手时还没解析出来（读到 0）**，早期探针若用它做 gate 需要就地重新 `PE_parse_boot_argn`。
