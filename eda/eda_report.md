# Problem C data audit

## Data01 acoustic measurements

- rows: 108, CallType counts: {'flat': 44, 'mod': 40, 'tv': 24}
- rows with all 6 complete features: 108
- F02 present iff CallType == tv: **True** (structural leakage)
- PulseRate absent iff CallType == flat: **False**

| feature | flat present | mod present | tv present |
|---|---|---|---|
| F02 | 0/44 | 0/40 | 24/24 |
| PulseRate | 0/44 | 34/40 | 20/24 |
| Duration | 44/44 | 40/40 | 24/24 |
| F01 | 44/44 | 40/40 | 24/24 |
| Fpeak | 44/44 | 40/40 | 24/24 |
| Q25 | 44/44 | 40/40 | 24/24 |
| Q50 | 44/44 | 40/40 | 24/24 |
| Q75 | 44/44 | 40/40 | 24/24 |

## Data02 playback experiments

- rows: 278; Type: {'call': 139, 'control': 139}; CallType: {'control': 139, 'tv': 58, 'flat': 48, 'mod': 33}
- Context: {'commuting': 130, 'searching': 76, 'after': 72}
- events: {'ResponseYesNo': 108, 'HeadsUpYesNo': 68, 'ApproachYesNo': 23, 'VocalYesNo': 81}
- Distance levels (13): [5, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120, 150, 200]
- Distance x CallType empty cells: 9 -> interaction terms are not estimable
- Npenguins median: 8.0
- response by Type: {'call': {'n': 139, 'responses': 90}, 'control': {'n': 139, 'responses': 18}}
- missing latencies (right-censored): {'HeadsUpLatency': 210, 'ApproachLatency': 250, 'VocalLatency': 193}

| Distance | control | flat | mod | tv |
|---|---|---|---|---|
| 5 | 3 | 3 | 0 | 0 |
| 10 | 2 | 0 | 1 | 0 |
| 20 | 3 | 0 | 2 | 2 |
| 30 | 2 | 2 | 2 | 1 |
| 40 | 7 | 2 | 3 | 7 |
| 50 | 19 | 4 | 8 | 9 |
| 60 | 23 | 7 | 3 | 6 |
| 70 | 3 | 1 | 0 | 2 |
| 80 | 34 | 11 | 4 | 14 |
| 100 | 22 | 14 | 5 | 11 |
| 120 | 1 | 0 | 2 | 0 |
| 150 | 8 | 3 | 3 | 2 |
| 200 | 12 | 1 | 0 | 4 |

## Data03-11 propagation correlations

- 9 files, 300 x 7 each; total NaN = 1350

| call | metric | NaN | median@4m | median@256m |
|---|---|---|---|---|
| flat | spectrogram | 140 | 0.916 | 0.138 |
| mod | spectrogram | 70 | 0.876 | 0.247 |
| tv | spectrogram | 240 | 0.829 | 0.311 |
| flat | amplitude_spectrum | 140 | 0.927 | 0.169 |
| mod | amplitude_spectrum | 70 | 0.881 | 0.263 |
| tv | amplitude_spectrum | 240 | 0.828 | 0.365 |
| flat | envelope | 140 | 0.683 | 0.163 |
| mod | envelope | 70 | 0.681 | 0.210 |
| tv | envelope | 240 | 0.627 | 0.141 |
