#!/usr/bin/env python3

import os
import argparse
import configparser
import time

# Set working dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set parser and ini file
cfg = configparser.ConfigParser()
cfg.read('resin.ini')

def time_offset_check():
    x = []
    for i in '+-':
        for j in range(0, 3):
            a = i + str(j)
            for k in range(0, 4):
                b = a + str(k)
                for l in range(0, 4, 3):
                    c = b + str(l) + '0'
                    x.append(c)
    return x

def add_sub_check(parser=cfg):
    if cfg.has_option('resin', 'max_resin') and cfg.has_option('resin', 'increment'):
        r_max = int(cfg.get('resin', 'max_resin'))
        r_inc = int(cfg.get('resin', 'increment'))
        return [i for i in range(r_inc, r_max + 1, r_inc)]
    else:
        return []

# Parse arguments
parser = argparse.ArgumentParser(description='Resin Calculator')
parser.add_argument('--resin', '-r', type=int)
parser.add_argument('--time-offset', type=str, choices=time_offset_check())
parser.add_argument('--DST', const=True, nargs='?', default=False, choices=['','True','False'])
parser.add_argument('--add', '-a', type=int, choices=add_sub_check())
parser.add_argument('--sub', '-s', type=int, choices=add_sub_check())
args = parser.parse_args()

w = False

# Set sections
if not cfg.has_section('resin'):
    cfg.add_section('resin')
    w = True
if not cfg.has_section('time'):
    cfg.add_section('time')
    w = True
if not cfg.has_section('variables'):
    cfg.add_section('variables')
    w = True

# Check resin ini
if not cfg.has_option('resin', 'max_resin'):
    cfg.set('resin', 'max_resin',  str(120))
    w = True
r_max = int(cfg.get('resin', 'max_resin'))
if not cfg.has_option('resin', 'resin_recharge'):
    cfg.set('resin', 'resin_recharge', str(8))
    w = True
r_recharge = int(cfg.get('resin', 'resin_recharge'))
if not cfg.has_option('resin', 'increment'):
    cfg.set('resin', 'increment', str(20))
    w = True
r_inc = int(cfg.get('resin', 'increment'))

# Check time ini
if args.time_offset: # --time-offset
    tz = str(args.time_offset)
    cfg.set('time', 'time_offset', str(tz))
    w = True
elif cfg.has_option('time', 'time_offset'):
    tz = cfg.get('time', 'time_offset')
else:
    cfg.set('time', 'time_offset', '+0000')
    tz = '+0000'
if args.DST: # --DST
    dst = bool(args.DST)
    cfg.set('time', 'DST', str(dst))
    w = True
elif cfg.has_option('time', 'DST'):
    dst = cfg.get('time', 'DST')
else:
    cfg.set('time', 'DST', 'False')
    dst = False

# Parse time-offset and DST
t_offset = (int(tz[1] + tz[2]) * 60 * 60) + (int(tz[3] + tz[4]) * 60)
if tz[0] == '-':
    t_offset = t_offset * -1
if bool(dst):
    if time.localtime()[8] == 1:
        t_offset += 3600

# Set time
t_now = time.time()

# Check init
if  not cfg.has_option('variables', 'init') or args.resin != None:
    t_init = t_now
    cfg.set('variables', 'init', str(t_init))
    w = True
else:
    t_init = float(cfg.get('variables', 'init'))

# Check resin
if args.resin != None:
    r = args.resin
    cfg.set('variables', 'resin_offset', str(r))
    w = True
elif cfg.has_option('variables', 'resin_offset'):
    r = int(cfg.get('variables', 'resin_offset'))
else:
    print('Error: No resin argument provided')
    exit()

# Calc amont of seconds since init
t_secs = t_now - t_init

# Calc recharge rate in seconds
t_recharge = r_recharge * 60

# Calc difference
r_regen = t_secs // t_recharge

# Calc next resin regen
r_next = str(t_secs / t_recharge).split('.')[1]

# Calc resin
r += r_regen

# Check if add or sub arg
if args.add and args.sub:
    print('Cannot add and subtract at the same time')
    exit(1)
elif args.add:
    r += args.add
    if r > r_max:
        print('Error: Cannot add more than max amount')
        exit(1)
elif args.sub:
    if r < args.sub:
        print('Error: Resin less than 0')
        exit(1)
    else:
        r -= args.sub

# Write vars
if str(int(r - r_regen)) != cfg.get('variables', 'resin_offset'):
    cfg.set('variables', 'resin_offset', str(int(r - r_regen)))
    w = True

print(f"Current time is {time.strftime('%H:%M:%S', time.localtime(t_now + t_offset))}")
if r >= r_max:
    print(f"Current resin is 120")
    print('Resin is capped')
else:
    print(f"Current resin is {int(r)}")
    print(f"Next resin at {str(int(r_next[0:2])) + '.' + r_next[3]}%")

# Print resin table
r_table = [i for i in range(r_inc, r_max + 1, r_inc)]
for i in r_table:
    if r < i:
        n = (i - r) * r_recharge * 60
        print(f"{i} resin at about {time.strftime('%H:%M', time.localtime(t_now + n + t_offset))}")

# Write to config file
if w == True:
    with open('resin.ini', 'w') as f:
        cfg.write(f)
        f.close()
    print('Written to config')