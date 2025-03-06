# visidata-uproot
[visidata](https://www.visidata.org) loader for [root](https://root.cern.ch) files, based on [uproot](https://github.com/scikit-hep/uproot5)

## Features

- [x] ROOT files
  - [x] subdirectoreis
  - [x] count of objects
- [x] TH
  - [x] TH1
    - [x] edges, heitghts
    - [x] errors, variance, counts
  - [x] TH2: matrix
- [ ] TTree
  - [x] simple ntuples
  - [ ] more complex types?
- [x] TGraph
  - [x] TGraph
  - [x] TGraphErrors
  - [x] TGraphAsymmErrors
- [x] TMatrixT
- [x] Other object:
    - [x] members dict

## Usage

- Copy `root.py` to `~/.visidata/`
- Edit `~/.visidatarc`

```python
import root # loads ~/.visidata/root.py
```
