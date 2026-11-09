# KK01 modules in build order, exec'd into the caller's namespace (later stages call earlier ones).
#     exec(open(os.path.join(<Construction>, "scripts", "kk01_load.py")).read())
# KK01_DIR may be set first. A function, class or upper-case constant defined twice across the modules is
# refused (a later def would silently replace an earlier one). Self-contained: no external skill scripts.
import ast as _ast
import os as _os
import bpy

KK01_MODULES = ("th_base.py", "kk01_struct.py", "kk01_beams.py", "kk01_floor.py", "kk01_cols.py", "kk01_walls.py", "kk01_roof.py", "kk01_cover.py", "kk01_ceiling.py", "kk01_paint.py", "kk01_tiles.py", "kk01_elec.py", "kk01_conduit.py", "kk01_units.py", "kk01_sanitary.py", "kk01_extras.py")
KK01_DIR = globals().get("KK01_DIR") or _os.path.join(_os.path.dirname(bpy.data.filepath), "scripts")
_srcs = [(_f, open(_os.path.join(KK01_DIR, _f), encoding="utf-8").read()) for _f in KK01_MODULES]
_seen = {}
for _f, _s in _srcs:
    for _n in _ast.parse(_s).body:
        _names = [_n.name] if isinstance(_n, (_ast.FunctionDef, _ast.ClassDef)) else \
            [_t.id for _t in getattr(_n, "targets", []) if isinstance(_t, _ast.Name) and _t.id.isupper()]
        for _nm in _names:
            assert _seen.setdefault(_nm, _f) == _f, f"{_nm} is defined in {_seen[_nm]} and {_f}"
for _f, _s in _srcs:
    exec(compile(_s, _os.path.join(KK01_DIR, _f) if _f.endswith(".py") else _f, "exec"))
