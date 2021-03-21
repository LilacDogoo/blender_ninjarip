"""
Author: LilacDogoo
"""

import datetime

lastUpdated = datetime.datetime(2021, 3, 20)
bl_info = {
    "name": "WRL Importer",
    "author": "LilacDogoo",
    "version": (1, 0, 0),
    "blender": (2, 91, 2),
    "category": "Import-Export",
    "location": "File > Import",
    "description": "Importer for RIP dumped by the \"Nemu64 Graphics\" plugin for \"Project 64\"."
}

# DEBUG MODE
debug = False

if "bpy" in locals():
    import importlib
    import lilacdogoo_blender_import_wrl
else:
    from lilacdogoo_blender_import_wrl import file_wrl

import bpy


def menu_func_import(self, context):
    self.layout.operator(file_wrl.BlenderOperator_wrl_import.bl_idname, text="N64 vrml (.wrl)")


_classes = (
    file_wrl.BlenderOperator_wrl_import,
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
