# apply-* patch index

Every `apply-NNN.py` is one experiment. Each script rewrites, in place, a single numbered
probe inside the PCIe bring-up driver (`hakios.pcie.c`), asserting that its anchor string
occurs exactly once before it replaces anything. Run in numeric order they reconstruct the
driver as it stood at the end of a session; individually they are the record of what was
tried and why.

**They are archived for traceability, not for replay.** The 5,150-line driver they were
written against did not survive the machine rebuild; the 43 KB snapshot in `src/` stops at
a much earlier patch. Treat this directory as the lab notebook, not as a patch series that
applies cleanly to anything in this repository.

| # | file | what it tried |
|---|---|---|
| 146 | `apply-146.py` | pcie.c: kmem_alloc_contig at the head of the boot path |
| 147 | `apply-147.py` | — |
| 148 | `apply-148.py` | — |
| 149 | `apply-149.py` | — |
| 150 | `apply-150.py` | 1) dma_init must keep the VA too |
| 150 | `apply-150b.py` | — |
| 151 | `apply-151a.py` | bar 21: print only, touch nothing |
| 151 | `apply-151b.py` | declare the constant right after the includes block: put it before the first "static uint32_t pcie_only" |
| 152 | `apply-152.py` | dma_init: read amss.bin and copy the first block |
| 152 | `apply-152b.py` | — |
| 153 | `apply-153.py` | — |
| 154 | `apply-154.py` | Silence every printf inside hakios_pcie_dma_init(): p140 showed that a single |
| 155 | `apply-155.py` | — |
| 156 | `apply-156.py` | — |
| 157 | `apply-157.py` | — |
| 158 | `apply-158.py` | — |
| 159 | `apply-159.py` | — |
| 160 | `apply-160.py` | — |
| 161 | `apply-161.py` | — |
| 162 | `apply-162.py` | — |
| 163 | `apply-163.py` | — |
| 164 | `apply-164.py` | — |
| 165 | `apply-165.py` | 1. extern declaration next to the other extern |
| 166 | `apply-166.py` | — |
| 167 | `apply-167.py` | — |
| 168 | `apply-168.py` | — |
| 169 | `apply-169.py` | — |
| 170 | `apply-170.py` | — |
| 171 | `apply-171.py` | — |
| 172 | `apply-172.py` | \tif (pcie_power_cycle) { |
| 173 | `apply-173.py` | hakios_pcie_dma_init(void) |
| 174 | `apply-174.py` | \t\t\t/* apply-174: bar0 is decoded by the memory window that dbi 0x20 names, |
| 175 | `apply-175.py` | \t\t\t\t/* apply-175: the endpoint can only fetch the image once it is a |
| 176 | `apply-176.py` | /* apply-176: the SMMU, the way star's lemonade_wifi.c does it (dma_prepare, |
| 177 | `apply-177.py` | if (!(rd(cb) & 1) && !(rd(cb + 0x58) & PCIE_SMMU_FAULT)) { |
| 178 | `apply-178.py` | printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128)); |
| 179 | `apply-179.py` | wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u \| PCIE_SMMU_STREAM); |
| 180 | `apply-180.py` | wr(smmu_mmio + 0x800 + 4 * smmu_match, 0xffff0000u); |
| 181 | `apply-181.py` | wr(bar0.base + 0x118, 1); |
| 182 | `apply-182.py` | if (ctrl & 2u) { |
| 183 | `apply-183.py` | wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u \| PCIE_SMMU_STREAM); |
| 184 | `apply-184.py` | wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u \| (1u << 16) \| 0x1c00u); |
| 184 | `apply-184b.py` | wr(smmu_cb + 0x7f0, 0); |
| 184 | `apply-184c.py` | wr(smmu_cb + 0x7f0, 0); |
| 185 | `apply-185.py` | wr(bar0.base + 0x12c, 0); |
| 186 | `apply-186.py` | printf("pcie: 5:   21: bhi id: ver 0x%08x maj 0x%08x serial 0x%08x anti 0x%08x segs 0x%08x hwid 0x%08x ivec 0x%08x\\n", |
| 187 | `apply-187.py` | — |
| 188 | `apply-188.py` | printf("pcie: 5:   21: bhie soc 0x%08x status 0x%08x\\n", |
| 189 | `apply-189.py` | wr(bar0.base + 0x224 + 0x34, PCIE_DMA_SIZE); |
| 190 | `apply-190.py` | — |
| 191 | `apply-191.py` | wr(bar0.base + 0x12c, 0); |
| 192 | `apply-192.py` | kr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, PAGE_MASK, 0, 0, |
| 193 | `apply-193.py` | kr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, 0, 0xfffff, 0, |
| 195 | `apply-195.py` | printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n", |
| 197 | `apply-197.py` | printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n", |
| 198 | `apply-198.py` | printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n", |
| 198 | `apply-198b.py` | wr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32)); |
| 199 | `apply-199.py` | printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n", |
| 202 | `apply-202.py` | 1) drop the MHI reset pulse: it restarts the BHI state machine right |
| 202 | `apply-202b.py` | 1) drop the MHI reset pulse (keep the ctrl/stat read and its printf). |
| 203 | `apply-203.py` | — |
| 204 | `apply-204.py` | 1. new macro next to the other SMMU ones |
| 205 | `apply-205.py` | pcie_note("bhie 0x%08x; ", st); |
| 206 | `apply-206.py` | — |
| 207 | `apply-207.py` | — |
| 208 | `apply-208.py` | — |
| 208 | `apply-208b.py` | — |
| 209 | `apply-209.py` | — |
| 210 | `apply-210.py` | — |
| 211 | `apply-211.py` | \t\t\t\t\tif (smmu_state == 1) { |
| 212 | `apply-212.py` | \t\t\t\t\tif (smmu_state == 1) { |
| 213 | `apply-213.py` | \t\t\t\t\t\tprintf("pcie: 5:   21: pt l1[2] 0x%016llx l2[256] 0x%016llx l3[4] 0x%016llx dma kvtophys 0x%llx\\n", |
| 214 | `apply-214.py` | — |
| 215 | `apply-215.py` | 1) 把 apply-205 的可写性测试包掉：它会写 0x12c，把 PBL 刚写下的 SUCCESS 冲掉 |
| 216 | `apply-216.py` | printf("pcie: 5:   21: bhi polls %u, status 0x%08x, mhi status 0x%08x (ready %u state %u)\\n", |
| 217 | `apply-217.py` | pcie_note("mhi ready %u status 0x%08x ee 0x%08x; ", |
| 218 | `apply-218a.py` | #define PCIE_SMMU_VEC_IOVA  0xa0084000ull |
| 218 | `apply-218b.py` | dma_init: allocate the 8 MiB image region right after the vector page. |
| 218 | `apply-218c.py` | static uint32_t pcie_dma_staged; |
| 219 | `apply-219.py` | — |
| 220 | `apply-220.py` | — |
| 221 | `apply-221.py` | — |
| 222 | `apply-222.py` | — |
| 223 | `apply-223.py` | \t\t\tif (pcie_bar == 21) { |
| 224 | `apply-224.py` | wr(bar0.base + 0x10c, 0u); |
| 225 | `apply-225.py` | printf("pcie: 5:   21: mhi ready after %u polls: status 0x%08x (ready %u state %u) ee 0x%08x\\n", |
| 226 | `apply-226.py` | /* apply-226: read the memory the PBL would have written the |
| 227 | `apply-227.py` | /* apply-227: zero the first 4 KiB of the SBL code segment while |
| 228 | `apply-228.py` | /* apply-228: fill the whole SBL code segment with "b ." so that |
| 229 | `apply-229.py` | — |
| 230 | `apply-230.py` | — |
| 231 | `apply-231.py` | — |
| 232 | `apply232.py` | \t\t\t\twr(bar0.base + 0x10c, |
| 233 | `apply233.py` | 0: the boot-time vote mask, without the pipe clock (star opens it after the phy) |
| 234 | `apply234.py` | — |
| 235 | `apply235.py` | 1) the mask variable |
| 236 | `apply236.py` | printf("pcie: 5:   21: apply-232: bhi gets addr 0x%llx size 0x%llx (fw 0x%llx)\\n", |
| 237 | `apply237.py` | for (i = 0; i < 100; i++) { |
| 238 | `apply238.py` | static uint32_t |
| 239 | `apply239.py` | wr(bar0.base + 0x224 + 0x30, |
| 240 | `apply240.py` | — |
| 241 | `apply241.py` | for (k2 = 1; k2 <= lw; k2++) { |
| 242 | `apply242.py` | — |
| 243 | `apply243.py` | — |
| 244 | `apply244.py` | — |
| 245 | `apply245.py` | static bool |
| 246 | `apply246.py` | \tif (PE_parse_boot_argn("pcie_headonly", &headonly, sizeof(headonly))) { |
| 246 | `apply246b.py` | \t\t\t\t/* |
| 247 | `apply247.py` | \t\t\t\t\tvm_offset_t mv = ml_io_map_unmappable( |
| 248 | `apply248.py` | \tfor (page = 0; page < PCIE_DMA_SIZE / 4096; page++) { |
| 249 | `apply249.py` | \t\t\t\t\twr(conf.base + 0x5c, 0u); |
| 250 | `apply250.py` | — |
| 251 | `apply251.py` | \t\t\t\t\t/* |
| 252 | `apply252.py` | \t\t\t\t/* |
| 253 | `apply253.py` | \t\t\t\t\t\t\tif (pcie_dma_extra != 0) { |
| 254 | `apply254.py` | \t\tprintf("pcie: stage: image 0x%x bytes at 0x%llx (iova 0x%llx), first word 0x%08x\\n", |
| 255 | `apply255.py` | \t\t\t\t\tfor (w = 0; w < 3000; w += 100) { |
| 256 | `apply256.py` | \t\t\t\t\t\t\t\tfor (k3 = 0; k3 < 0x8000; k3 += 64) { |
| 257 | `apply257.py` | — |
| 258 | `apply258.py` | — |
| 259 | `apply259.py` | — |
| 260 | `apply260.py` | — |
| 261 | `apply261.py` | /* apply-261: the ring watch runs in the middle of the run, but the log ring |
| 262 | `apply262.py` | \t\t\t\t\tprintf("pcie: 5:   21: apply-252 t=0 ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n", |
| 262 | `apply262b.py` | close the two extra braces where the old single brace closed |
| 263 | `apply263.py` | \t\t\t\t\tprintf("pcie: 5:   21: apply-263 right after the bhie bell: mh 0x%08x ee 0x%08x err 0x%08x\\n", |
| 264 | `apply264.py` | \t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 before init: mh 0x%08x ee 0x%08x cfg 0x%08x ctrl 0x%08x\\n", |
| 265 | `apply265.py` | — |
| 266 | `apply266.py` | parse it in the same place as the other mhi args |
| 267 | `apply267.py` | wr(bar0.base + 0x84, (uint32_t)(lo >> 32)); |
| 268 | `apply268.py` | — |
| 269 | `apply269.py` | \t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, (uint32_t)rb); |
| 270 | `apply270.py` | \t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_nobase", &want2, sizeof(want2)); |
| 271 | `apply271.py` | \t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2)); |
| 272 | `apply272.py` | \t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1) { |
| 273 | `apply273.py` | \t\t\t\t\t\t\tif (pcie_mhi_nom0 == 0) { |
| 274 | `apply274.py` | — |
| 275 | `apply275.py` | wr(pcie_dma_extra + 0x2400 + 0x28, (uint32_t)cwp); |
| 276 | `apply276.py` | \t\t\t\t\t\t\twant2 = 0; |
| 277 | `apply277.py` | wr(bar0.base + 0x10, (cf & 0x0000ffffu) \| (3u << 16)); |
| 278 | `apply278.py` | — |
| 279 | `apply279.py` | — |
| 280 | `apply280.py` | find bhie printf line index |
| 281 | `apply281.py` | 1) 把 apply-280 的打印重复一份到 apply-225 final 之前（日志尾部，不会被 GPU 刷屏挤掉） |
| 282 | `apply282.py` | — |
| 283 | `apply283.py` | — |
| 284 | `apply284.py` | — |
| 285 | `apply285.py` | — |
| 286 | `apply286.py` | — |
| 287 | `apply287.py` | — |
| 288 | `apply288.py` | — |
| 289 | `apply289.py` | — |
| 290 | `apply290.py` | — |
| 291 | `apply291.py` | — |
| 292 | `apply292.py` | — |
| 293 | `apply293.py` | — |
| 294 | `apply294.py` | — |
| 295 | `apply295.py` | — |
| 296 | `apply296.py` | uint32_t d9; |
| 297 | `apply297.py` | — |
| 298 | `apply298.py` | — |
| 299 | `apply299.py` | — |
| 300 | `apply300.py` | — |
| 301 | `apply301.py` | — |
| 302 | `apply302.py` | if (smmu_state == 1 && pcie_dma_extra != 0) { |
| 303 | `apply303.py` | — |
| 304 | `apply304.py` | 1. declare the boot-arg variable next to the other mhi switches |
| 304 | `apply304b.py` | — |
| 305 | `apply305.py` | — |
| 306 | `apply306.py` | the tre ring and its host-side offset |
| 306 | `apply306b.py` | — |
| 307 | `apply307.py` | — |
| 308 | `apply308.py` | -*- coding: utf-8 -*- |
| 309 | `apply309.py` | -*- coding: utf-8 -*- |
| 310 | `apply310.py` | — |
| 311 | `apply311.py` | — |
| 312 | `apply312.py` | 1. declaration after pcie_mhi_data (line 89 style: with a comment) |
| 313 | `apply313.py` | — |
| 314 | `apply314.py` | — |
| 315 | `apply315.py` | \t\t\t\t\t/* apply-315: the vendor walks m2 -> m0 through mhi_set_mhi_state() |
| 316 | `apply316.py` | — |
| 317 | `apply317.py` | — |
| 318 | `apply318.py` | — |
| 319 | `apply319.py` | printf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n", |
| 320 | `apply320.py` | — |
| 321 | `apply321.py` | /* apply-321: the vendor queues its first data TRE 1.5 ms |
| 322 | `apply322.py` | — |
| 323 | `apply323.py` | find the end of that printf statement: the next line containing ');' after i |
| 324 | `apply324.py` | only the one inside the er loop (the first occurrence) gets the per-ring length |
| 325 | `apply325.py` | — |
| 326 | `apply326.py` | — |
| 327 | `apply327.py` | 1) statics for the deferred print |
| 327 | `apply327b.py` | — |
| 328 | `apply328.py` | parse the two boot args next to the apply-314 parse |
| 329 | `apply329.py` | 1) drop the old tail print block (7 lines starting with the dc ivac before apply-327 tail printf) |
| 330 | `apply330.py` | wr(dbi.base + 0xa0, (control & ~0xfu) \| 1u); |
| 330 | `apply330probe.py` | — |
| 331 | `apply331.py` | — |
| 332 | `apply332.py` | — |
| 333 | `apply333.py` | — |
| 334 | `apply334.py` | retarget RDDM away from the firmware image copy (which spans 0xa0220000..0xa071fa50) |
| 334 | `apply334b.py` | — |
| 335 | `apply335.py` | — |
| 335 | `apply335g.py` | — |
| 335 | `apply335h.py` | — |
| 335 | `apply335i.py` | — |
| 335 | `apply335j.py` | — |
| 336 | `apply336.py` | find the closing of the apply-252 done printf statement (ends with ');') |
| 336 | `apply336b.py` | — |
| 336 | `apply336c.py` | — |
| 337 | `apply337.py` | — |
| 338 | `apply338.py` | 1. declaration |
| 339 | `apply339.py` | — |
| 340 | `apply340.py` | find the comment line containing marker |
| 341 | `apply341.py` | revert apply-338 gate |
| 345 | `apply345.py` | 定位块边界：apply-332 注释行 到 apply-333 hits 打印行；apply-335 enter 到其块尾 |
| 346 | `apply346.py` | 只关掉后面的那个（数据实验块），保留前面那个较早的同名判断 |
| 347 | `apply347.py` | — |
| 348 | `apply348.py` | — |
| 349 | `apply349.py` | printf("pcie: 5:   21: apply-237 done after %u ms, errdbg %08x %08x %08x\\n", |
| 350 | `apply350.py` | insert only at the occurrence inside the apply-251 block (the one followed later by apply-264 after m0) |
| 351 | `apply351.py` | want2 = 0; |
| 351 | `apply351b.py` | — |
| 352 | `apply352.py` | printf("apply-335 d: flushed\\n"); |
| 354 | `apply354.py` | — |
| 355 | `apply355.py` | — |
| 356 | `apply356.py` | — |
| 357 | `apply357.py` | — |
| 358 | `apply358.py` | — |
| 359 | `apply359.py` | — |
| 360 | `apply360.py` | — |
| 361 | `apply361.py` | 1. declaration |
| 361 | `apply361b.py` | — |
| 362 | `apply362.py` | 1. declarations |
| 363 | `apply363.py` | printf("pcie: 5:   21: apply-362 m0 the moment ee 2 showed: mh 0x%08x ctrl 0x%08x after %u ms\\n", |
| 363 | `apply363b.py` | — |
| 364 | `apply364.py` | {	/* apply-364: raw context words, so we can see what the device |
| 365 | `apply365.py` | if (pcie_erfull >= 2u) {	/* apply-365: wipe the er ring before the ee 2 |
| 366 | `apply366.py` | rd(pcie_dma_extra + 20 * 0x30 + 0x20), rd(pcie_dma_extra + 20 * 0x30 + 0x28)); |
| 367 | `apply367.py` | declare + parse |
| 368 | `apply368.py` | — |
| 369 | `apply369.py` | — |
| 370 | `apply370.py` | — |
| 371 | `apply371.py` | — |
| 372 | `apply372.py` | — |
| 373 | `apply373.py` | — |
| 374 | `apply374.py` | — |
| 375 | `apply375.py` | — |
| 376 | `apply376.py` | — |
| 377 | `apply377.py` | — |
| 378 | `apply378.py` | — |
| 379 | `apply379.py` | the fetch question. |
| 380 | `apply380.py` | is the command ring really being read, this round. |
| 381 | `apply381.py` | stop cancelling our own start command. |
| 382 | `apply382.py` | does the device fetch data TREs at all? |
| 383 | `apply383.py` | where does the device think the channel contexts live? |
| 384 | `apply384.py` | does anything read channel 20's doorbell, and does the device answer a |
| 385 | `apply385.py` | catch RDDM, read the BHI window while we are there, and try to keep it. |
| 386 | `apply386.py` | is the channel data path off for every channel, or only for ch20? |
| 387 | `apply387.py` | same question as apply-386, but without the static array. |
| 388 | `apply388.py` | the apply-386/387 question, with the pointer bug fixed. |
| 389 | `apply389.py` | the same host code, three channels - LOOPBACK (ch0), DIAG (ch4), IPCR (ch20). |
| 390 | `apply390.py` | close the loop - arm LOOPBACK RX (ch1) with two buffers, send on ch0, look |
| 391 | `apply391.py` | is there a firmware client on ch20/ch21 at all? |
| 392 | `apply392.py` | does anything fetch ch20 at all? |
| 393 | `apply393.py` | what does the firmware think of itself?  Read-only register dump. |
| 394 | `apply394.py` | 1 ms sampling of ch20/ch21 from the moment AMSS is up (data=17). |
| 395 | `apply395.py` | (data=18): arm BHIE RX, then force the device into RDDM and take the dump. |
| 396 | `apply396.py` | (data=19): does the channel doorbell need a device-wake pulse first? |
| 397 | `apply397.py` | (data=20): give ch20 the ring the vendor driver actually gives it - 64 elements. |
| 398 | `apply398.py` | plan B -- give the endpoint a working MSI and see if that changes anything. |
| 399 | `apply399.py` | read the BHI block where it actually lives. |
| 400 | `apply400.py` | arm BHIE RX *before* the BHI download, then force RDDM and see if a dump lands. |
| 401 | `apply401.py` | the pre-download block never ran -- drop the smmu_state term and prove reach. |
| 402 | `apply402.py` | the pre-download block was gated on pcie_mhi_data, which is still 0 there. |
| 403 | `apply403.py` | the stock stack does not sit in M0, it sits in M2. |
| 404 | `apply404.py` | do what star's ipcr_probe() does, step for step. |
| 405 | `apply405.py` | isolate which step pushes the firmware into RDDM. |
| 406 | `apply406.py` | keep the firmware's own ch20 ring, put a TRE there, then START_CHAN again. |
| 407 | `apply407.py` | the legal way to (re)start a channel - RESET_CHAN first, then START_CHAN. |
| 408 | `apply408.py` | when the firmware asserts, ask it why - dump the whole BHI block. |
| 409 | `apply409.py` | read every event ring, not just the two we have been staring at. |
| 410 | `apply410.py` | fix the pointer truncation in apply-409 (it panicked the kernel). |
| 411 | `apply411.py` | assert BT_EN (pin 65) and SW_CTRL (pin 153) together with WLAN_EN. |
| 412 | `apply412.py` | is the firmware just slow?  Watch the IPCR channels for ten seconds. |
| 413 | `apply413.py` | the one host action we never did -- a real MHICTRL reset before boot. |
| 414 | `apply414.py` | ring the ch20 doorbell properly and then wait ten full seconds. |
| 415 | `apply415.py` | send the one command the vendor sends after mission mode and we never did. |
| 416 | `apply416.py` | acknowledge the events we read, the way a real host does. |
| 417 | `apply417.py` | make every channel idle, then ask for M2. |
| 418 | `apply418.py` | start the ipcr channel late instead of in the honeymoon. |
| 419 | `apply419.py` | the ipcr ring, tried after the settle window. |
| 420 | `apply420.py` | START_CHAN(20) after the settle, then immediately a TRE. |
| 421 | `apply421.py` | the clean host-side open: ENABLED, START, then a TRE. |
| 422 | `apply422.py` | list every entry the command DB carries. |
| 423 | `apply423.py` | does the firmware create the IPCR channel contexts by itself? |
| 424 | `apply424.py` | hand the firmware a TRE without touching its channel context. |
| 425 | `apply425.py` | the one transition we never tried with the firmware's own contexts - M0 -> M2. |
| 426 | `apply426.py` | the vendor's order - M0 first, then ring the channel doorbell. |
| 427 | `apply427.py` | brstmode. |
| 428 | `apply428.py` | restore MHICFG.NHWER and clear IEOT in the data TRE. |
| 429 | `apply429.py` | event ring "empty" convention - wp starts at the LAST element. |
| 430 | `apply430.py` | replicate star's post-mission IPCR bring-up, with completion checks. |
| 431 | `apply431.py` | publish chstate 0 in the early context write, the way star does. |
| 432 | `apply432.py` | make the starflow block wait for EE=2 before it touches anything. |
| 433 | `apply433.py` | pcie_chzero=2 leaves LOOPBACK/DIAG running but publishes IPCR as disabled. |
| 434 | `apply434.py` | pcie_chzero=3 publishes the IPCR pair as chstate 1 (ENABLED), not 2. |

Total: **307 scripts**, numbers 146–434, 281 distinct numbers (180 with an explicit one-line description in the script itself).

Numbering was assigned per round, so `b`/`c` suffixes and repeated numbers are normal: a round
that was re-run with a different approach kept its number. The file name is the identity.
