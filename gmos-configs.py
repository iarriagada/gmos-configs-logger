#!/usr/bin/env python3

import os
import sys
import argparse
import epics
import time
import h5py
import re
import numpy as np

from datetime import datetime, timedelta, timezone, tzinfo

def ca_cfg_extract(cacfg_file):
    print('EPICS_CA_ADDR_LIST = {}'.format(os.environ['EPICS_CA_ADDR_LIST']))
    cat_filt = re.compile(r'^(status|command) [a-z]+::([a-zA-Z]+)')
    ignore_filt = re.compile(r'^([#{}]|apply\b)')
    rec_filt = re.compile(
        r'^([a-zA-Z0-9_]+)[ ]+([a-zA-Z0-9:]+(\.[A-Z]+)*)[ ]*([^.]+)*$'
    )
    zero_filt = re.compile(r'^0[ ]+')

    cfg_list = {}

    with open(cacfg_file, 'r') as f:
        ca_cfg = f.readlines()

    for l in ca_cfg:
        line = (l.strip()).replace('\t',' ')
        if not(line):
            continue
        ignore_res = ignore_filt.match(line)
        if ignore_res:
            continue
        cat_res = cat_filt.match(line)
        if cat_res:
            element = cat_res.group(1)
            el_name = cat_res.group(2)
            continue
        rec_res = rec_filt.search(line)
        if rec_res:
            record = rec_res.group(2)
            rec_name = rec_res.group(1)
            rec_desc = zero_filt.split(str(rec_res.group(4)))[-1]
            print(f"Connecting to {record}...", end='\r')
            chan = epics.PV(record)
            time.sleep(0.25) # needed to give the PV object time to connect
            print(f"Connecting to {record}... Connected!")
            cfg_list[record] = {'tag':rec_name,
                                'pv':chan,
                                'desc':rec_desc,
                                'type':element,
                                'type_name':el_name}

    return cfg_list

def on_change(pvname=None, value=None, timestamp=None, **kw):
    if kw['start_flag'][0]:
        ts = datetime.strftime(datetime.fromtimestamp(timestamp),
                               "%Y%m%dT%H:%M:%S.%f")
        ts_str = f"[{ts}]"
        cmdsts_str = f"[{kw['channels'][pvname]['type']}]"
        cmdsts_name_str = f"[{kw[channels][pvname]['type_name']}]"
        chan_str = f"[{kw[channels][pvname]['desc']}]"
        pv_str = f" {pvname} = {value}"
        print(ts_str + cmdsts_str + cmdsts_name_str + chan_str + pv_str)


if __name__ == '__main__':
    chan_list = ca_cfg_extract('gmos.ca')
    for sn in chan_list:
        cmd_sts_line = f"[{chan_list[sn]['type']}][{chan_list[sn]['type_name']}]"
        rec_line = f"[{chan_list[sn]['desc']}] {sn}"
        print(cmd_sts_line + rec_line)






