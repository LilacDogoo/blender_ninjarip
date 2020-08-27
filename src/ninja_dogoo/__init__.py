"""
Author: LilacDogoo
"""

import datetime

lastUpdated = datetime.datetime(2020, 8, 26)
bl_info = {
    "name": "NinjaRipper (Dogoo Version)",
    "author": "LilacDogoo",
    "version": (1, 0, 0),
    "blender": (2, 83, 0),
    "category": "Import-Export",
    "location": "File > Import",
    "description": "Importer for RIP dumped by NinjaRipper."
}

# DEBUG MODE
debug = False

if "bpy" in locals():
    import importlib
    import ninja_dogoo

    importlib.reload(ninja_dogoo.utils.binary_file)
else:
    from ninja_dogoo.utils import binary_file
    from ninja_dogoo import file_ninja_rip

import bpy


def menu_func_import(self, context):
    self.layout.operator(file_ninja_rip.BlenderOperator_NinjaRIP_import.bl_idname, text="NinjaRipper (Dogoo Version) (.rip)")


_classes = (
    file_ninja_rip.BlenderOperator_NinjaRIP_import,
)


def register():
    # Register all classes contained in this package so that Blender has access to them
    from bpy.utils import register_class
    for cls in _classes:
        register_class(cls)

    # Add menu items
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    # Remove menu items
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    # Unregister classes
    for cls in _classes:
        bpy.utils.unregister_class(cls)
