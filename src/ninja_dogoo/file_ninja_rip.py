"""
Author: LilacDogoo

This adds an 'Import from RIP menu item' in the 'import' menu in Blender.
This also hold all the capabilities of reading NinjaRipper [RIP] files into a 'PreBlender_Model' object.

This script was written by me (LilacDogoo).
"""

import os
import math
import time
from typing import BinaryIO, List

import bmesh
import bpy

import ninja_dogoo
from ninja_dogoo.utils import binary_file


class BlenderOperator_NinjaRIP_import(bpy.types.Operator):
    bl_idname = "import_scene.rip"
    bl_label = "NinjaRipper (Dogoo Version)"
    bl_description = "Import Models from NinjaRipper Dumps."
    bl_options = {'UNDO'}

    # Properties used by the file browser
    filepath: bpy.props.StringProperty(name="File Path", description="The file path used for importing the RIP files",
                                       maxlen=1024, default="", options={'HIDDEN'})
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN'})
    directory: bpy.props.StringProperty(maxlen=1024, default="", subtype='FILE_PATH', options={'HIDDEN'})
    filter_folder: bpy.props.BoolProperty(name="Filter Folders", description="", default=True, options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.rip", options={'HIDDEN'})

    # Custom Properties used by the file browser
    # p_load_textures_and_materials: bpy.props.BoolProperty(name="Load Textures and Materials",
    #                                                       description="Attempts to load textures.",
    #                                                       default=True)
    # p_cull_back_facing: bpy.props.BoolProperty(name="Cull Backfaces",
    #                                            description="Generally enabled for video games models. Keep in mind, Models from these games are intended to 'back-face cull. Faces will exist in the exact same positions but have opposite normals.",
    #                                            default=True)

    # p_merge_vertices: bpy.props.BoolProperty(name="Merge Vertices",
    #                                          description="The original model is all individual triangles. This will attempt to create a continuous 'connected' mesh. Slow.",
    #                                          default=False)
    # p_parse_motion: bpy.props.BoolProperty(name="Parse Armature Animation",
    #                                                    description="For models that have animation data, an attempt will be made to parse it.\nCurrently not working",
    #                                                    default=False)

    def invoke(self, context, event):
        self.directory = "C:\\Z_NinjaRipper"
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        time_start = time.time()  # Operation Timer
        # Iterate through all slected files
        for file in self.files:
            # Extract RIP file into Model Object
            model: PreBlender_Model = read_ninja_rip(directory=self.directory, filename=file.name)
            to_blender(model, file.name, option_import_location=bpy.context.scene.cursor.location)

        time_end = time.time()  # Operation Timer
        print("    Completed in %.4f seconds" % (time_end - time_start))
        return {'FINISHED'}


class VertexDescriptor:
    def __init__(self, R: ninja_dogoo.utils.binary_file.LD_BinaryReader, vertex_attribute_count: int):
        super().__init__()
        self.element_length = 0
        self.enabled_uv: bool = False
        self.enabled_color: bool = False
        self.enabled_colorAlpha: bool = False
        self.enabled_normal: bool = False

        self.x: int = -1
        self.y: int = -1
        self.z: int = -1
        self.u: int = -1
        self.v: int = -1
        self.r: int = -1
        self.g: int = -1
        self.b: int = -1
        self.a: int = -1
        self.nx: int = -1
        self.ny: int = -1
        self.nz: int = -1

        for i in range(vertex_attribute_count):
            name: str = R.read_string()
            R.seek(4)  # Skip Unknown
            # The file has byteLength, I want 4byteLength since all values are float and floats are 4 bytes
            offset: int = int(R.read_long_unsigned() / 4)
            length: int = R.read_long_unsigned()
            element_count: int = R.read_long_unsigned()
            for j in range(element_count):
                R.seek(4)  # Skip unknown for each element

            self.element_length += element_count
            if name == "POSITION":
                self.x = offset
                self.y = offset + 1
                self.z = offset + 2
            if name == "NORMAL":
                self.enabled_normal = True
                self.nx = offset
                self.ny = offset + 1
                self.nz = offset + 2
            elif name == "COLOR":
                self.enabled_color = True
                self.r = offset
                self.g = offset + 1
                self.b = offset + 2
                if element_count == 4:
                    self.enabled_colorAlpha = True
                    self.a = offset + 3
            elif name == "TEXCOORD":
                self.enabled_uv = True
                self.u = offset
                self.v = offset + 1


class PreBlender_Model:
    def __init__(self, R: ninja_dogoo.utils.binary_file.LD_BinaryReader) -> None:
        super().__init__()
        num_of_triangles = R.read_long_unsigned()
        vertex_count = R.read_long_unsigned()
        byte_stride = R.read_long_unsigned()
        num_of_textures = R.read_long_unsigned()
        file_header_6 = R.read_long_unsigned()
        vertex_attribute_count = R.read_long_unsigned()
        # Buffers
        self.vertDesc: VertexDescriptor = VertexDescriptor(R, vertex_attribute_count)
        self.raw_vertices: List[List[float]] = []
        self.faces: List[List[int]] = []

        # Only keep last texture. I've only ever seen 1 texture so I don't know how to handle multiple
        for i in range(num_of_textures):
            self.texture_name = R.read_string()

        for i in range(num_of_triangles):
            self.faces.append([R.read_long_unsigned(), R.read_long_unsigned(), R.read_long_unsigned()])

        float_stride = int(byte_stride / 4)
        for i in range(vertex_count):
            self.raw_vertices.append([R.read_float() for _ in range(float_stride)])

        i = 0

    def getVertexPosition(self, index: int) -> tuple:
        RV = self.raw_vertices[index]
        # Return values are out of order to attain a rotation without matrix multiplying.
        return RV[self.vertDesc.x], -RV[self.vertDesc.z], RV[self.vertDesc.y]

    def getVertexNormal(self, index: int) -> tuple:
        RV = self.raw_vertices[index]
        return RV[self.vertDesc.nx], RV[self.vertDesc.ny], RV[self.vertDesc.nz]

    def getVertexColor(self, index: int) -> tuple:
        RV = self.raw_vertices[index]
        if self.vertDesc.enabled_colorAlpha:
            return RV[self.vertDesc.r], RV[self.vertDesc.g], RV[self.vertDesc.b], RV[self.vertDesc.a]
        return RV[self.vertDesc.r], RV[self.vertDesc.g], RV[self.vertDesc.b], 1

    def getVertexTexCoord(self, index: int) -> tuple:
        # print("index:%i", index)
        RV = self.raw_vertices[index]
        # print(RV)
        # print("u:%i   v:%i", (self.vertDesc.u, self.vertDesc.v))
        return RV[self.vertDesc.u], RV[self.vertDesc.v]

    def hasNormals(self):
        return self.vertDesc.enabled_normal

    def hasColors(self):
        return self.vertDesc.enabled_color

    def hasAlphas(self):
        return self.vertDesc.enabled_colorAlpha

    def hasTexCoords(self):
        return self.vertDesc.enabled_uv


def read_ninja_rip(directory: str, filename: str) -> PreBlender_Model:
    filepath: str = os.path.join(directory, filename)

    # Begin Parsing File
    f: BinaryIO = open(filepath, 'rb')

    # Reads the first 4 bytes of the files and checks for the signature
    if ninja_dogoo.utils.binary_file.read_long_unsigned_big_endian(f) != 0xDEC0ADDE:
        print("ERROR: File signature did not match RIP Signature \"0xDEC0ADDE\"" + filepath)
        f.close()
        return None

    R: binary_file.LD_BinaryReader = binary_file.LD_BinaryReader(f, False)  # Little Endian
    ninja_rip_file_version = R.read_long_unsigned()

    return PreBlender_Model(R)


def to_blender(model: PreBlender_Model, name: str, option_import_location=(0, 0, 0)):
    if model is None:
        return

    # CREATE BLENDER STUFF
    blender_mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    blender_object: bpy.types.Object = bpy.data.objects.new(name, blender_mesh)
    blender_bMesh: bmesh.types.BMesh = bmesh.new()
    blender_bMesh.from_mesh(blender_mesh)

    # Add Data to Face Loops (UV, Color)
    blender_bMesh_uvLayer = blender_bMesh.loops.layers.uv.new()
    blender_bMesh_colorLayer = blender_bMesh.loops.layers.color.new()

    # Create Vertices
    DEG_TO_RAD = math.pi / 180  # TODO do I need this?
    blender_bMesh_verts = []  # Need to access this to create faces
    for vertex_index in range(len(model.raw_vertices)):
        blender_bMesh_verts.append(blender_bMesh.verts.new(model.getVertexPosition(vertex_index)))
    blender_bMesh.verts.index_update()

    # Create Faces
    for face in model.faces:
        blender_face_loop = []
        for vertex_index in face:  # Loops through the vertices in this Face Loop
            blender_face_loop.append(blender_bMesh_verts[vertex_index])  # Converts to Blender format
        blender_bMesh_face: bmesh.types.BMFace = blender_bMesh.faces.new(blender_face_loop)
        # Assign UV coords, Vertex Color
        for vertex_index, loop_vertex in enumerate(blender_bMesh_face.loops):  # Loops through the vertices in this BMesh Face Loop
            VI = face[vertex_index]
            # UV coordinates
            loop_vertex[blender_bMesh_uvLayer].uv = model.getVertexTexCoord(VI)
            # Vertex Colors
            loop_vertex[blender_bMesh_colorLayer] = model.getVertexColor(VI)

    # Push BMesh to Mesh
    blender_bMesh.to_mesh(blender_mesh)
    blender_bMesh.free()

    # Some Mesh Data must be added after conversion from BMesh to Mesh

    # Assign Normals
    blender_mesh.use_auto_smooth = True
    # Set normal vectors to (0, 0, 0) to keep auto normal - Maybe implement this

    blender_normals: List[float] = []
    for face in model.faces:
        for vertex_index in face:
            n = model.getVertexNormal(vertex_index)
            blender_normals.append(n)
    blender_mesh.normals_split_custom_set(blender_normals)
    # blender_mesh.normals_split_custom_set([c.normal for c in model.vertices])  # Old way - works with models that do not reuse vertices

    bpy.context.scene.collection.objects.link(blender_object)
    # bpy.ops.object.mode_set()  # TODO Why do I not need this??

    # TODO add support for the dds textures


if __name__ == "__main__":
    read_ninja_rip("C:\\Z_NinjaRipper\\2020.08.25_02.17.51_Dolphin.exe_16844\\2020.08.25_02.19.02_Dolphin.exe", "Mesh_0000.rip")
