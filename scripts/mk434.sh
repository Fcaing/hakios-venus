#!/bin/bash
cd /mnt/c/Users/Administrator/Documents/deepseek-harness/default-workspace/venus-recon
RET=200 bash mk-pcie2.sh p434 'pcie=1 pcie_step=5 pcie_power=1 pcie_delay=0 pcie_settle=100 pcie_bar=21 pcie_watch=0 pcie_star_mask=31 pcie_bhi_addr=0xa0004000 pcie_bhi_size=0x80000 pcie_novec=1 pcie_msi_test=1 pcie_mhi_nom0=1 pcie_chanstart=1 pcie_mhi_late0=1 pcie_mhi_data=16 pcie_bw_db=1 pcie_bw_rp=1 pcie_gen=2'
