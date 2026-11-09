# -*- coding: utf-8 -*-
"""Shared basics for the stage modules (thunder-house, own implementation). Loaded first by kk01_load.py."""
import bpy


def mat(name, rgb, rough=0.5, metal=0.0, transmission=0.0, emission=0.0):
    """Get-or-create a Principled BSDF material `name`: base colour rgb (linear), roughness, metallic, glass-like
    transmission and self-emission strength. diffuse_color mirrors the colour for the viewport / Workbench."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None:
        b = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        out = next(n for n in m.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
        m.node_tree.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    ins = b.inputs
    ins["Base Color"].default_value = (*rgb, 1.0)
    ins["Roughness"].default_value = rough
    ins["Metallic"].default_value = metal
    for k in ("Transmission Weight", "Transmission"):
        if k in ins:
            ins[k].default_value = transmission
            break
    if emission:
        for k in ("Emission Color", "Emission"):
            if k in ins:
                ins[k].default_value = (*rgb, 1.0)
                break
        if "Emission Strength" in ins:
            ins["Emission Strength"].default_value = emission
    m.diffuse_color = (*rgb, 1.0)
    m.roughness, m.metallic = rough, metal
    return m
