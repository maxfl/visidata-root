from visidata import (
    BaseSheet,
    Column,
    ItemColumn,
    Path,
    Progress,
    PyobjSheet,
    SequenceSheet,
    Sheet,
    VisiData,
    anytype,
    vd,
)


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
                Column(
                    "type", type=str, getter=lambda col, row: type(row.source).__name__
                ),
                Column("nItems", type=int, getter=_get_source_nitems),
            ]
            self.recalc()
            for k, v in source.iteritems(recursive=False):
                yield ROOTSheet(self.name, k, source=v)
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
        elif isinstance(source, uproot.behaviors.TH1.TH1):
            flow = True
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
        else:
            self._colum_names = None
            vd.fail("unknown root object type %s" % type(source))

    def openRow(self, row):
        if isinstance(row, BaseSheet):
            return row

        # from .npy import NpySheet
        from visidata.loaders.npy import NpySheet

        if isinstance(row, tuple):
            if self._colum_names is not None:
                return PyobjSheet("test", source=dict(zip(self._colum_names, row)))
            else:
                return PyobjSheet("test", source=row)

        vd.fail(f"unimplemented openRow type {type(row).__name__}, {row}")


def _get_type(dt) -> type:
    dtype_str = dt.str
    if "i" in dtype_str or "u" in dtype_str:
        return int
    elif "f" in dtype_str:
        return float

    return anytype


def _get_source_name(col, row) -> str:
    try:
        return row.source.name
    except AttributeError:
        pass

    try:
        return row.source.path[-1]
    except AttributeError:
        pass

    return "???"


def _get_source_nitems(col, row):
    source = row.source
    uproot = vd.importExternal("uproot")

    if isinstance(source, uproot.behaviors.TTree.TTree):
        return source.member("fEntries")
    elif isinstance(source, uproot.behaviors.TH1.TH1):
        return source.axes[0].member("fNbins")

    return len(source)


ROOTSheet.addCommand(
    "A",
    "dive-metadata",
    'vd.push(SheetDict(cursorRow.name + "_attrs", source=cursorRow.attrs))',
    "open metadata sheet for object referenced in current row",
)
