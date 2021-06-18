#!/usr/bin/env python3

import os
import re
import sys
import epics
import time

from datetime import datetime, timedelta, timezone, tzinfo

def ca_cfg_extract(cacfg_file):
    print('EPICS_CA_ADDR_LIST = {}'.format(os.environ['EPICS_CA_ADDR_LIST']))
    # cat_filt = re.compile(r'^[ ]*(status|command) [a-z]+::([a-zA-Z]+)')
    cat_filt = re.compile(r'^[ ]*(status|command) ([a-zA-Z]+)')
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

def ca_monitors(chan_list):
    abort_flag = False
    enable_flag = [False]
    ops_log = []
    wait_time = 0.005
    if not(chan_list):
        sys.exit("Empty channels list. Aborting")
    # print("Initiliazing monitors... ", end='\r')
    for cn in chan_list:
        print(f"{cn} = {chan_list[cn]['pv'].value}")
        chan_list[cn]['pv'].add_callback(on_change, en_flag=enable_flag,
                                           channels=chan_list, log=ops_log)
    print("Initiliazing monitors... Done")
    enable_flag[0] = True
    print("Monitors enabled, starting capture")
    start_time = datetime.timestamp(datetime.now())
    curr_time = start_time
    print('To stop capture now: <Ctrl>-c')
    try:
        while (curr_time - start_time) < 28800:
            time.sleep(wait_time)
            curr_time = datetime.timestamp(datetime.now())
    except KeyboardInterrupt as err:
        choice = input("Generate log file? (Y/n): ")
        if choice in ['N', 'n']:
            abort_flag = True
    finally:
        if abort_flag:
            sys.exit('Aborting capture')
        # Stop the monitors. We don't want to continue capturing data
        enable_flag[0] = False
        for cn in chan_list:
            chan_list[cn]['pv'].clear_callbacks()
        ops_log[-1] = ops_log[-1].strip()
        return ops_log

def on_change(pvname=None, value=None, timestamp=None, **kw):
    if kw['en_flag'][0]:
        ts = datetime.strftime(datetime.fromtimestamp(timestamp),
                               "%Y%m%dT%H:%M:%S.%f")
        ts_str = f"[{ts}]"
        cmdsts_str = f"[{kw['channels'][pvname]['type']}]"
        cmdsts_name_str = f"[{kw['channels'][pvname]['type_name']}]"
        chan_str = f"[{kw['channels'][pvname]['desc']}]"
        pv_str = f" {pvname} = {value}"
        log_line = ts_str + cmdsts_str + cmdsts_name_str + chan_str + pv_str
        print(log_line)
        kw['log'].append(log_line + "\n")

if __name__ == '__main__':
    ca_file = 'gmos.ca'
    # ca_file = 'seqexec.ca.TCS'
    chan_list = ca_cfg_extract(ca_file)
    observation_log = ca_monitors(chan_list)
    observation_log.sort()
    curr_date = datetime.strftime(datetime.now(), "%Y%m%dT%H%M%S")
    file_name = f"obs_log_{curr_date}.log"
    print(f"Writing file: {file_name}...", end='\r')
    with open(file_name, 'w') as f:
        for l in observation_log:
            f.write(l)
    print(f"Writing file: {file_name}... Done")
    # for sn in chan_list:
        # cmd_sts_line = f"[{chan_list[sn]['type']}][{chan_list[sn]['type_name']}]"
        # rec_line = f"[{chan_list[sn]['desc']}] {sn}"
        # print(cmd_sts_line + rec_line)






