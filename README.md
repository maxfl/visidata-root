# visidata-uproot
[visidata](https://www.visidata.org) loader for [root](https://root.cern.ch) files, based on [uproot](https://github.com/scikit-hep/uproot5)

## Features

- [x] ROOT files
  - [x] subdirectoreis
  - [x] count of objects
- [ ] TH
  - [x] TH1
    - [x] edges, heitghts
    - [x] errors, variance, counts
  - [x] TH2
  - [ ] TH3
- [ ] TTree
  - [x] simple ntuples
- [x] TGraph
  - [x] TGraph
  - [x] TGraphErrors
  - [x] TGraphAsymmErrors

## TODO

- Option to read underflow/overflow
- Bins for TH2

## Usage

- Copy `root.py` to `~/.visidata/`
- Edit `~/.visidatarc`

```python
import root # loads ~/.visidata/root.py
```
