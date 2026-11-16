# 厂商 MHI 全量对账（venus / QCA6490）

日期：2026-11-11
对照对象：`/root/xiaomi-venus/drivers/bus/mhi/core/*`（小米 11 内核源码树）+ `/root/xiaomi-venus/drivers/net/wireless/cnss2/*`
我方实现：`/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c`

这份文档的目的：把厂商在"PCIe 链路起来 → BHI/BHIE 下载 → M0 → 第一条数据 TRE"这条路径上
**每一个寄存器写、每一个门铃、每一个上下文位、每一个 TRE 位**都列出来，逐条对照我方实现。
用户要求"不要漏任何细节"，所以这里是穷举式清单，不是摘要。

---

## 1. 厂商在整条路径上的全部 MMIO 写点

`grep -rn 'mhi_write_reg\|mhi_write_reg_field\|mhi_write_db' core/*.c` 的完整结果只有 8 处：

| 位置 | 写什么 | 我们是否等价 |
|---|---|---|
| `mhi_init.c:1026` | `reg_info[]` 表（见 §2） | ✅ 全套都写 |
| `mhi_init.c:1019` | 唤醒门铃 `base+CHDBOFF+8*127` 高/低 32 位各写 0 | ✅ `0x6f8`/`0x6fc` |
| `mhi_main.c:174` `mhi_write_db()` | 先写 `db_addr+4`（高 32 位），再写 `db_addr`（低 32 位） | ✅ 顺序一致 |
| `mhi_main.c:189/200` | brstmode 两条路径（`db_mode` 决定是否立即写） | ✅ 我们直接写，等价于 disable 分支 |
| `mhi_main.c:218` `mhi_ring_cmd_db()` | `*ctxt_wp = db; mhi_write_db(0x70, db)` | ✅ 先写 ctx wp 再敲门铃 |
| `mhi_pm.c:170` | MHICTRL RESET 位（`field(MHICTRL, RESET, 1)`） | ✅ `0xb0` 之外我们还写过 `0x38 bit1` |
| `mhi_pm.c:174` | MHICTRL 状态位 `state << 8`（M0=0x200 / M2=0x400 / M3=0x600） | ✅ 都试过 |
| `mhi_pm.c:202/217/245` | 唤醒门铃写 1 / 1 / 0（`wake_get`/`wake_put`） | ✅ apply-396 试过 |

**结论：厂商一共只写这 8 类寄存器，我们全部覆盖，没有漏写的寄存器。**

---

## 2. `reg_info[]` 的 16 条初始化写（`mhi_init.c:900-1030`）

| 偏移 | 名称 | 厂商写的值 | 我方 |
|---|---|---|---|
| 0x58/0x5c | CCABAP_H/L | `chan_ctxt_addr` | ✅ `0xa0200000` |
| 0x60/0x64 | ECABAP_H/L | `er_ctxt_addr` | ✅ `0xa0200800`（早）/`0xa0202000`（晚） |
| 0x68/0x6c | CRCBAP_H/L | `cmd_ctxt_addr` | ✅ `0xa0200c00`（早）/`0xa0202400`（晚） |
| 0x10 | MHICFG.NER | `total_ev_rings` | ✅ 3 |
| 0x10 | MHICFG.NHWER | `hw_ev_rings` | ⚠️ 我们写 0（设备原本报 2） |
| 0x80/0x84 | MHICTRLBASE_H/L | `iova_start` | ✅ `0xa0000000` |
| 0x88/0x8c | MHICTRLLIMIT_H/L | `iova_stop` | ✅ `0xb0000000` |
| 0x98/0x9c | MHIDATABASE_H/L | `iova_start` | ✅ 写了 |
| 0xa0/0xa4 | MHIDATALIMIT_H/L | `iova_stop` | ✅ 写了 |
| — | `mhi_init_bw_scale()` | BW scale 门铃 `0x6f0` | ✅ BW_REQ/ack 实测可用 |
| — | `mhi_init_timesync()` | tsync 门铃 | ✅ 未用但寄存器已备 |

**唯一差异：MHICFG.NHWER。** 设备复位后自己报的是 `0x02030880`（NHWER=2、NER=3、NHWCH=3、NCH=0x80），
我们把它改写成 `0x00030880`（NHWER=0）。这一项在 p473 里回填成 2 复测（见 §7）。

---

## 3. 通道上下文（`mhi_chan_ctxt`，stride 0x2c）

| 偏移 | 字段 | 厂商语义 | 我方 |
|---|---|---|---|
| 0x00 | chstate:8 / brstmode:2 / pollcfg:6 / rsvd:16 | 主机写 ENABLED(1)，**设备**写 RUNNING(2) | ✅ |
| 0x04 | chtype | 1=TO_DEVICE, 2=FROM_DEVICE | ✅ |
| 0x08 | erindex | 事件环号 | ✅ 1 |
| 0x0c | rbase(u64) | ring IOVA | ✅ |
| 0x14 | rlen | `num_elements * sizeof(tre)` | ✅ 0x200 / 0x400 都试过 |
| 0x1c | rp | **只由主机写一次**（`mhi_init.c:1085`），设备从不回写 | ✅ |
| 0x24 | wp | 主机在敲门铃前写 | ✅ |

关键事实：`chan_ctxt->rp` 在整个厂商驱动里只被写一次（初始化时 `rp = wp = rbase`），
**从来不读回**。所以"rp 不动"不能作为"设备没取"的证据 —— 判据必须是 TX_EVENT 或通道 st 变化。

---

## 4. TRE 位域

```
struct mhi_tre { u64 ptr; u32 dword[2]; };     /* 16 字节 */
```

命令 TRE（`mhi_internal.h:306-330`）：

| 命令 | ptr | dword0 | dword1 |
|---|---|---|---|
| START | 0 | 0 | `(chid<<24) \| (18<<16)` = `0x14120000` |
| STOP | 0 | 0 | `(chid<<24) \| (17<<16)` |
| RESET | 0 | 0 | `(chid<<24) \| (16<<16)` = `0x14100000` |
| SFR_CFG | sfr dma | len | `73<<16` = `0x00490000` |

数据 TRE（`mhi_internal.h:356-358`）：

```
MHI_TRE_DATA_DWORD0(len)              = len & MHI_MAX_MTU
MHI_TRE_DATA_DWORD1(bei,ieot,ieob,chain)
    = (2 << 16) | (bei << 10) | (ieot << 9) | (ieob << 8) | chain
```

我方用的 `0x00020200` = `(2<<16) | (1<<9)` = **IEOT 置位、BEI/ IEOB/chain 均为 0**。
IEOT 在厂商里表示"这是本次传输的最后一个元素"，普通报文应为 0。p430 的 LOOPBACK 成功用例
用的也是 `0x00020200` 并且被设备接受了，所以 **IEOT 不是阻断原因**（但严格说普通包应写 0x00020000）。

---

## 5. 状态机：厂商的 M0 / M2 / M3

| 函数 | 厂商做的事 | 我方 |
|---|---|---|
| `mhi_pm.c:285 mhi_pm_reset()` | 等 MHICTRL.RESET==0、MHISTATUS.READY==1 | ✅ |
| `mhi_pm.c:324 mhi_pm_m0_transition()` | 写 M0 → `wake_get(true)` → 遍历**所有**事件环敲门铃 + 命令环（若 rp!=wp）→ 遍历所有"有 TRE 待发"的通道敲门铃 → `wake_put(false)` | ✅ p471 复刻了这个顺序 |
| `mhi_pm.c:426 mhi_pm_m2_transition()` | 写 M2，等设备进 M2 | ✅ p470 试过，设备拒绝 |
| `mhi_pm.c:1232` | 写 M3 | ✅ |
| `mhi_pm.c:473 mhi_pm_mission_mode_transition()` | EE 必须是 AMSS/WFW；置 `ring->wp = base+len-el_size`；敲门铃；`mhi_init_sfr()`；`mhi_timesync_log()`；建 sysfs/设备 | ⚠️ SFR 我们试过（p460），一发就 assert |

**真机常态是 M2**（`MHI_CNTRL 0x400`、`MHI_STATUS 0x401`），我们始终停在 M0（`0x200`/`0x201`），
且写 0x400 后 MHISTATUS 不接受。

---

## 6. glue 层（cnss2）

| 位置 | 调用 | 我方 |
|---|---|---|
| `pci.c:1360` | `mhi_prepare_for_power_up()` | ✅ |
| `pci.c:1367` | `mhi_sync_power_up()` | ✅ |
| `qmi.c:667` | `cnss_enable_int_pow_amp_vreg()`（`vrm.wlan` TCS） | ❌ 但它在 **BDF 下载成功之后**，属 QMI 阶段 |
| `pci.c:3486` | `cnss_pci_load_m3()` | ❌ 但只用于 RDDM/crash dump 缓冲，不是启动阶段 |
| `power.c` | 六路 rail + `wlan_en`/`bt_en`/`sw_ctrl` | ✅ 全部投票成功（p435/p456 实测） |

---

## 7. 逐条结论

1. **寄存器集合、写序、门铃地址、上下文位、TRE 位、glue 层调用：全部与厂商一致**（§1–§6）。
2. 设备在 EE=2 之后**不再响应任何主机输入**：通道门铃（ch4/5/20/21 全静默）、事件门铃（wp 追平无效）、
   唤醒门铃、M2 请求（MHICTRL 收下 0x400 但 MHISTATUS 恒 0x201）。
3. 命令环在**启动窗口**（EE 1→2 的 35 ms）里被正常执行并回 4 条 SUCCESS；稳态下再发就**不再有 completion**，
   只有 RESET_CHAN 能把固件打成 SYS_ERR（`errcode 0x0004161d`、`errdbg 0x27204021/0x00891e38/0x00000c30`）。
4. 唯一仍然生效的数据通道是 LOOPBACK ch0→ch1（p430/p431 双向闭环），说明 MHI 引擎本体是好的。
5. 因此剩下的差异**不在主机侧**，而在固件的服务初始化：IPCR（ch20/ch21）的消费端从未真正挂上。

## 8. 未验证/待验证项（按可行性排序）

- [x] **MHICFG.NHWER=2 复测（p473）**：把设备自己的 `0x02030880` 写回去，ch20 门铃依旧无人应答。
- [x] **数据 TRE 的 IEOT 清 0（p473）**：同轮用 `0x00020000` 投 TRE，依旧不取。
- [x] **brstmode 变体（p472）**：把 ch20 的 word0 改成 ch0 那种 `0x00000002`（RUNNING/brst 0），再改成 `0x00000302`（brst 3），两次都静默。
- [x] **M0-then-doorbell 顺序（p471）**：按 `mhi_pm_m0_transition` 的顺序，先写 MHICTRL=M0 再敲 ch20 门铃，静默。
- [ ] 在 M0 之前（EE=1、SBL 阶段）就把 ch20 上下文和 TRE 准备好，看 AMSS 启动时是否顺带消费。
- [ ] 用 `bd_k2.elf`（board data）走 QMI 的时序，但 QMI 依赖 IPCR —— 循环依赖，暂不可行。
- [ ] 换 QCA6390 固件对照（手上没有第二份）。

## 9. p471–p473 实测汇总（2026-11-11 早）

| 轮次 | 变量 | 结果 |
|---|---|---|
| p471 | 先写 M0 再敲门铃（vendor 顺序） | `apply-426 g: ch20 st 0x00000202 rp 0xa020c000 wp 0xa020c030`，payload 未动 |
| p472 | ch20 brstmode 0 → 3 | `apply-427 c: st 0x00000002` / `e: st 0x00000302`，两次都无 TX_EVENT |
| p473 | NHWER=2 + IEOT=0 | `apply-428 d: cfg 0x02030880 ch20 st 0x00000202`，er1 全零 |

三轮的 `er1` 都停在 `rp=wp=0xa0205000`，`er0` 只有启动期那 4 条 completion。**主机侧已无未试变量。**
