
## 十四、M8 深水区：p391–p416（2026-11-10 上午）

### 14.1 结论一句话

控制面（EE/M0/RESET）、命令环上下行、事件环设备→主机全部可用；**数据通道 ch20/ch21 在 AMSS(EE=2) 之后从未被设备认领**。所有“配置类”假设已逐条证伪，问题被收敛到“AMSS 的 MHI 客户端没有完成初始化”这一条上。

### 14.2 状态机实验（全部无效）

| 轮次 | 做法 | 结果 |
|---|---|---|
| p392 | `pcie_mission=1`，建完通道后写 state 4 | `ctrl 0x400` 写进去了，`MHISTATUS` 仍是 `0x201` |
| p393 | apply-356 逐级 2→1→4 | 两次请求都被无声丢弃，`mh` 恒 `0x201` |
| p394 | `pcie_mhi_state_val=1`，从 M0 直接要 M3(4) | 同样被无视 |
| p399 | apply-361 `pcie_noearlystate`：EE=2 之前一次都不写 MHICTRL | 设备照样 inert，早写不是元凶 |
| p400 | apply-362 `pcie_ee2m0=1`：EE=2 后 1 ms 内写 M0 | `mh 0x201` 正常，但 ER 仍只有 2 条 |
| p402 | apply-363 `pcie_ee2m0=2`：完整 RESET 脉冲（写 1 → 等 → 写回 0 → 再 M0） | 设备确实进 reset 又自己出来，ER 仍 2 条 |

### 14.3 事件环真相（p395/p396/p397/p405）

- 擦净实验（apply-365 把 `0x4000..0x5000` 清零后）设备仍写回 2 条 TRE ⇒ **事件环设备→主机通路是通的**，那 2 条是设备真写的（STATE_CHANGE `0x20` + EE_EVENT `0x40`）。
- 设备**从不更新事件上下文里的 wp(0x24)**（擦净后 rp/wp 都还是基址）⇒ 主机只能扫 TRE 判断有无新事件。
- wp 初值（`rb+0xff0` vs `rb`，p396）与搬家（p397 A/B）都与事件数无关；p348 那轮 `er0[2]` 的 `0x21` 很可能是同一块物理内存上一轮残留。

### 14.4 通道上下文的正确语义（vendor `mhi_internal.h:261`）

```
struct mhi_chan_ctxt {
	u32 chstate:8; u32 brstmode:2; u32 pollcfg:6; u32 reserved:16;  /* 0x00 */
	u32 chtype;   /* 0x04 = mhi_chan->type            */
	u32 erindex;  /* 0x08 = mhi_chan->er_index（不是 ee！）*/
	u64 rbase 0x0c | u64 rlen 0x14 | u64 rp 0x1c | u64 wp 0x24
};  /* stride 0x2c */
```
- `ch20[00]=0x00000002` 是设备写的 **chstate=RUNNING**；
- 我们此前写的 “ee=2” 实际改的是 **erindex**；
- `mhi_cmd_ctxt` 的三个 u32 全是 reserved，命令环 `0x04` 写 0 或 1 **都不影响**（p414 对照实验：写 0 也照样收到 4 条 COMPLETION）⇒ 之前“`type=1` 修好命令环”是**假阳性**，已把默认值改回 0；
- 数据 TRE `0x00020200 = (2<<16)|(1<<9)` 与 `MHI_TRE_DATA_DWORD1(bei,1,0,0)` 一致，格式正确。

### 14.5 DTB 里的通道配置（`/tmp/venus2.dts:12892` 起）

```
mhi,max-channels = <0x1e>;  mhi,buffer-len = <0x8000>;  mhi,m2-no-db-access;

mhi_chan@20 { reg=<0x14>; event-ring=<0x01>; chan-dir=<0x01>; data-type=<0x01>; doorbell-mode=<0x02>; ee=<0x14>; auto-start; };  /* IPCR TX */
mhi_chan@21 { reg=<0x15>; event-ring=<0x01>; chan-dir=<0x02>; data-type=<0x00>; doorbell-mode=<0x02>; ee=<0x14>; auto-queue; auto-start; };  /* IPCR RX */
```
p415（apply-375）按此把 `chtype=1/0`、`erindex=1`、`chstate=1` 写进上下文，读回全部正确，结果仍是：

```
apply-375 dtb ctxt: c20 00000001 00000001 00000001 c21 00000001 00000000 00000001 mh 0xc7264ff3
apply-317 rang again: ch20 rp 0xa020c000 wp 0xa020c020 mh 0x00000201
apply-360 ch20 state after 200 ms: 0x00000001 (1 = device inert)   ← 设备连认领都不做
```

⇒ **上下文内容不是触发条件**。

### 14.6 其它已关闭的点

- **IMGSIZE**：p416 显示写入前它已经是 `0x80000`（与真机 `BHI_IMGADDR 0xa1e80000 / IMGSIZE 0x80000` 一致），5 MB 只是我们自己摆进 DDR 的镜像，两者无关。
- **`mhi,m2-no-db-access`**（`mhi_init.c:1511-1513`）：venus 的 `db_access` 只有 M0，`MHI_DB_ACCESS_VALID` 在 M2 为假，vendor 驱动在 M2 下**不会** `mhi_ring_chan_db`。我们一直在 M0(`0x201`) 下敲门铃，这一条尚未构成矛盾，但值得在下一轮作为“设备也许在等 wake 而不是门铃”的线索。
- **门铃写序**：apply-300 起已是 vendor 语义（先 `+4` 再低半），无需改。

### 14.7 下一步（按性价比）

1. 拿 star/lemonade 的**成功 dmesg 全量**（尤其 `mhi` 初始化 0–600 ms 段）做逐字段 diff；真机只能在 MISSION 后读寄存器，读不到启动中间态。
2. 比对 BHI→BHIE 时间线（vendor 有 `BHI transfer complete` 的时间戳）。
3. 若确认 AMSS 没起来：检查是否缺 `mhi_patch`/`linkReqQ` 之外的前置（DTB 里 `ee=<0x14>`、`event-ring=1` 已给全）。
