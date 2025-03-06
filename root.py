from itertools import chain

from visidata import (
    BaseSheet,
    Column,
    ItemColumn,
    Path,
    Progress,
    PyobjSheet,
    Sheet,
    SheetDict,
    VisiData,
    anytype,
    vd,
)

vd.option("root_th1_flow", False, "read undrflow/overflow for TH1")
vd.option("root_th2_flow", False, "read undrflow/overflow for TH1")


@VisiData.api
def open_root(vd, p):
    return ROOTSheet(p.base_stem, source=p)


@VisiData.api
def guess_root(vd, p):
    if p.open_text().read(8).startswith("root"):
        return dict(filetype="root")


VisiData.open_root = VisiData.open_root


class ROOTSheet(Sheet):
    "Support sheets in ROOT format."

    _colum_names = None

    def iterload(self):
        uproot = vd.importExternal("uproot")
        source = self.source
        if isinstance(self.source, Path):
            source = uproot.open(str(self.source))

        self.columns = []
        if isinstance(source, uproot.reading.ReadOnlyDirectory):
            self.rowtype = "sheets"
            source_name = source.path[-1] if source.path else source.file_path

            self.columns = [
                Column(
                    source_name,
                    type=str,
                    getter=_get_source_name,
                    keycol=1,
                ),
                Column("type", type=str, getter=_get_source_type),
                Column("nItems", type=int, getter=_get_source_nitems),
            ]
            self.recalc()
            for k, v in source.iteritems(recursive=False):
                if isinstance(
                    v,
                    (
                        uproot.behaviors.TTree.TTree,
                        uproot.behaviors.TH2.TH2,
                        uproot.behaviors.TH1.TH1,
                        uproot.behaviors.TGraph.TGraph,
                        uproot.behaviors.TGraphErrors.TGraphErrors,
                        uproot.behaviors.TGraphAsymmErrors.TGraphAsymmErrors,
                    ),
                ):
                    yield ROOTSheet(self.name, k, source=v)
                else:
                    members = v.all_members
                    yield PyobjSheet(
                        self.name, k, source=dict(type=type(v).__name__, **members)
                    )
            self._colum_names = None
        elif isinstance(source, uproot.behaviors.TTree.TTree):
            arrays = source.arrays(library="np")
            size = source.member("fEntries")
            self._colum_names = []
            for i, (name, array) in enumerate(arrays.items()):
                type_str = _get_type(array.dtype)
                self.addColumn(ItemColumn(name, i, type=type_str, width=8), index=i)
                self._colum_names.append(name)
            self.recalc()
            yield from Progress(zip(*arrays.values()), total=size)
        elif isinstance(source, uproot.behaviors.TH2.TH2):
            flow = self.options.get("root_th2_flow")
            heights, edges_x, edges_y = source.to_numpy(flow=flow)
            type_str = _get_type(heights.dtype)

            nrows = heights.shape[0]
            ncols = heights.shape[1]

            def rowname(i):
                if i == 0:
                    return "x-"
                elif i == nrows - 1:
                    return "x+"

                return f"y_{i-1}"

            self.addColumn(ItemColumn("x", 0, width=8, keycol=1), index=0)
            for i in range(ncols):
                if i == 0:
                    yname = "y-"
                elif i == ncols - 1:
                    yname = "y+"
                else:
                    yname = f"y_{i-1}"
                self.addColumn(
                    ItemColumn(yname, i + 1, type=type_str, width=8), index=i + 1
                )
            self.recalc()
            yield from Progress(
                (
                    list(chain((name,), hrow))
                    for name, hrow in zip(map(rowname, range(nrows)), heights)
                ),
                total=nrows,
            )
        elif isinstance(source, uproot.behaviors.TH1.TH1):
            flow = self.options.get("root_th1_flow")
            heights, edges = source.to_numpy(flow=flow)
            left = edges[:-1]
            right = edges[1:]

            arrays = {
                "left": left,
                "right": right,
                "center": 0.5 * (left + right),
                "height": heights,
                "counts": source.counts(flow=flow),
                "width": (right - left),
            }

            if source.weighted:
                arrays["error"] = source.errors(flow=flow)
                arrays["variance"] = source.variances(flow=flow)
            self._colum_names = list(arrays)

            for i, (name, array) in enumerate(arrays.items()):
                type_str = _get_type(array.dtype)
                self.addColumn(ItemColumn(name, i, type=type_str, width=8), index=i)
            self.recalc()
            yield from Progress(zip(*arrays.values()), total=len(heights))

        elif isinstance(
            source,
            (
                uproot.behaviors.TGraph.TGraph,
                uproot.behaviors.TGraphErrors.TGraphErrors,
                uproot.behaviors.TGraphAsymmErrors.TGraphAsymmErrors,
            ),
        ):
            npoints = source.all_members["fNpoints"]
            arrays = {
                "x": source.all_members["fX"],
                "y": source.all_members["fY"],
            }
            if isinstance(source, uproot.behaviors.TGraphErrors.TGraphErrors):
                arrays["ex"] = source.all_members["fEX"]
                arrays["ey"] = source.all_members["fEY"]
            elif isinstance(
                source, uproot.behaviors.TGraphAsymmErrors.TGraphAsymmErrors
            ):
                arrays["ex_low"] = source.all_members["fEXlow"]
                arrays["ex_high"] = source.all_members["fEXhigh"]
                arrays["ey_low"] = source.all_members["fEYlow"]
                arrays["ey_high"] = source.all_members["fEYhigh"]

            for i, (name, array) in enumerate(arrays.items()):
                type_str = _get_type(array.dtype)
                self.addColumn(ItemColumn(name, i, type=type_str, width=8), index=i)
            self.recalc()
            yield from Progress(zip(*arrays.values()), total=npoints)
        else:
            self._colum_names = None
            vd.fail("unknown root object type %s" % type(source))

    def openRow(self, row):
        if isinstance(row, BaseSheet):
            return row

        vd.fail(f"unimplemented openRow type {type(row).__name__}, {row}")


def _get_type(dt) -> type:
    dtype_str = dt.str
    if "i" in dtype_str or "u" in dtype_str:
        return int
    elif "f" in dtype_str:
        return float

    return anytype


def _get_source_type(col, row):
    match row:
        case SheetDict():
            return row.source["type"]

    return type(row.source).__name__


def _get_source_name(col, row) -> str:
    return row.names[-1]


def _get_source_nitems(col, row):
    source = row.source
    uproot = vd.importExternal("uproot")

    if isinstance(source, uproot.behaviors.TTree.TTree):
        return source.member("fEntries")
    elif isinstance(source, uproot.behaviors.TH2.TH2):
        return source.axes[0].member("fNbins")
    elif isinstance(source, uproot.behaviors.TH1.TH1):
        return source.axes[0].member("fNbins")
    elif isinstance(
        source,
        (
            uproot.behaviors.TGraph.TGraph,
            uproot.behaviors.TGraphErrors.TGraphErrors,
            uproot.behaviors.TGraphAsymmErrors.TGraphAsymmErrors,
        ),
    ):
        return source.all_members["fNpoints"]

    return len(source)


ROOTSheet.addCommand(
    "A",
    "dive-metadata",
    'vd.push(SheetDict(cursorRow.name + "_attrs", source=cursorRow.attrs))',
    "open metadata sheet for object referenced in current row",
)
