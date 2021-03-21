"""
Author: LilacDogoo

This adds an 'Import from RIP menu item' in the 'import' menu in Blender.
This also hold all the capabilities of reading NinjaRipper [RIP] files into a 'PreBlender_Model' object.

This script was written by me (LilacDogoo).
"""
from typing import List, TextIO, BinaryIO

import os
import time
import random

import bpy
import bmesh

import lilacdogoo_blender_import_wrl


class BlenderOperator_wrl_import(bpy.types.Operator):
    bl_idname = "import_scene.wrl"
    bl_label = "N64 VRML Importer"
    bl_description = "Import Models from Nemu64 vrml dumps."
    bl_options = {'UNDO'}

    # Properties used by the file browser
    filepath: bpy.props.StringProperty(name="File Path", description="The file path used for importing the wrl file",
                                       maxlen=1024, default="", options={'HIDDEN'})
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN'})  # ????
    directory: bpy.props.StringProperty(maxlen=1024, default="", subtype='FILE_PATH', options={'HIDDEN'})
    filter_folder: bpy.props.BoolProperty(name="Filter Folders", description="", default=True, options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.wrl", options={'HIDDEN'})

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
        self.directory = "C:\\VRML"
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        time_start = time.time()  # Operation Timer

        scene: PreBlender_Scene = read_wrl_file(directory=self.directory, filename=self.filepath)
        to_blender(scene)

        time_end = time.time()  # Operation Timer
        print("    Completed in %.4f seconds" % (time_end - time_start))
        return {'FINISHED'}


class PreBlender_Material:
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "NoNameAssigned"
        self.index: int = -1
        self.ambient_intensity: float = 1
        self.diffuse_color: (float, float, float) = (1.0, 1.0, 1.0)
        self.specular_color: (float, float, float) = (1.0, 1.0, 1.0)  # TODO not implemented, not sure where it is even used yet
        self.emissive_color: (float, float, float) = (0.0, 0.0, 0.0)
        self.alpha: float = 1
        self.texture_url: str = None
        self.texture_repeat: bool = True
        self.first_mesh_linked = None


def preBlender_Material_equals(A: PreBlender_Material, B: PreBlender_Material) -> bool:
    if A.texture_url != B.texture_url: return False
    if A.texture_repeat != B.texture_repeat: return False
    if A.diffuse_color != B.diffuse_color: return False
    if A.emissive_color != B.emissive_color: return False
    if A.alpha != B.alpha: return False
    if A.ambient_intensity != B.ambient_intensity: return False
    return True


class PreBlender_Mesh:
    def __init__(self) -> None:
        super().__init__()
        self.name = None
        self.points: List[(float, float, float)] = []
        self.texcoords: List[(float, float)] = []
        self.colors: List[(float, float, float)] = []
        self.material: PreBlender_Material = None


class PreBlender_Scene:
    def __init__(self) -> None:
        super().__init__()
        self.directory: str = ""
        self.filename: str = ""
        self.materials: List[PreBlender_Material] = []
        self.meshes: List[PreBlender_Mesh] = []


def read_wrl_file(directory: str = "C:\\VRML\\", filename: str = "output.wrl") -> PreBlender_Scene:
    scene = PreBlender_Scene()
    scene.directory = directory
    scene.filename = filename
    filepath: str = os.path.join(directory, filename)
    if lilacdogoo_blender_import_wrl.debug: print(filepath)
    # Begin Parsing File
    f: TextIO = open(filepath, 'r', encoding='UTF-8')
    content = f.readlines()
    if len(content) == 0: return None
    i: int = 0
    while i < len(content):
        s: List[str] = content[i].split()
        if (len(s) > 0) and (s[0] == "Shape") and (s[1] == "{"):  # Shape
            material = PreBlender_Material()
            mesh = PreBlender_Mesh()
            i += 1
            s = content[i].split()
            while not s[0] == "}":
                if s[0] == "appearance":  # Material
                    material.name = s[2]
                    i += 1
                    s = content[i].split()
                    while not s[0] == "}":
                        if s[0] == "material":  # Material Parameters
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "ambientIntensity": material.ambient_intensity = float(s[1])
                                if s[0] == "diffuseColor": material.diffuse_color = [float(s[1]), float(s[2]), float(s[3])]
                                if s[0] == "specularColor": material.specular_color = [float(s[1]), float(s[2]), float(s[3])]
                                if s[0] == "emisiveColor": material.emisive_color = [float(s[1]), float(s[2]), float(s[3])]
                                if s[0] == "shinines": material.specular = float(s[1])
                                if s[0] == "transparency": material.alpha = 1 - float(s[1])
                                i += 1
                                s = content[i].split()
                        if s[0] == "texture":  # Texture Parameters
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "url": material.texture_url = s[1].strip("\"")
                                if s[0] == "repeatS": material.texture_repeat = s[1] == "TRUE"
                                i += 1
                                s = content[i].split()
                        i += 1
                        s = content[i].split()
                if s[0] == "geometry":  # Mesh
                    mesh.name = s[2]
                    i += 1
                    s = content[i].split()
                    while not s[0] == "}":
                        if s[0] == "coord":  # Mesh Verticies
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "point":
                                    i += 1
                                    s = content[i].split()
                                    while not s[0] == "]":
                                        # Load Rotated so it is upright in Blender
                                        mesh.points.append((float(s[0]), -float(s[2].strip(",")), float(s[1])))
                                        i += 1
                                        s = content[i].split()
                                i += 1
                                s = content[i].split()
                        if s[0] == "texCoord":  # Mesh Texture Coordinates
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "point":
                                    i += 1
                                    s = content[i].split()
                                    while not s[0] == "]":
                                        mesh.texcoords.append((float(s[0]), float(s[1].strip(","))))
                                        i += 1
                                        s = content[i].split()
                                i += 1
                                s = content[i].split()
                        if s[0] == "color":  # Mesh Texture Coordinates
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "color":
                                    i += 1
                                    s = content[i].split()
                                    while not s[0] == "]":
                                        mesh.colors.append((float(s[0]), float(s[1]), float(s[2].strip(","))))
                                        i += 1
                                        s = content[i].split()
                                i += 1
                                s = content[i].split()
                        i += 1
                        s = content[i].split()
                i += 1
                s = content[i].split()

            # Search for Duplicate Material
            _mat_dupe_: bool = False
            for _mat_ in scene.materials:
                if preBlender_Material_equals(_mat_, material):
                    material = _mat_  # use the duplicate instead
                    _mat_dupe_ = True
                    break
            # if no duplicate found then append
            if _mat_dupe_ is not None:
                material.index = len(scene.materials)
                scene.materials.append(material)
            # Assign Material to Mesh
            mesh.material = material
            # Link mesh to material IF none already - For usage with some shader defaults.
            if mesh.material.first_mesh_linked is None:
                mesh.material.first_mesh_linked = mesh

            scene.meshes.append(mesh)
        i += 1
    f.close()
    return scene


# Pretty hack but should work relieably.
# Skip the header then check if every single byte after is zero.
def is_BMP_valid_transparency(path: str) -> bool:
    f: BinaryIO = open(os.path.join(path), 'rb')
    f.seek(0x36)
    b = f.read(1)
    while len(b) > 0:
        if b[0] > 0: return True
        b = f.read(1)
    return False


def to_blender(scene: PreBlender_Scene):
    if scene is None: return
    r = random.Random()
    blenderMaterials: List[bpy.types.Material] = []
    for mat in scene.materials:
        blenderMaterial: bpy.types.Material = bpy.data.materials.new(mat.name)
        blenderMaterial.diffuse_color = (r.random(), r.random(), r.random(), 1.0)
        blenderMaterial.use_backface_culling = True
        blenderMaterial.use_nodes = True

        # ▬ NODES ▬
        # Principled BSDF
        nodes: bpy.types.Nodes = blenderMaterial.node_tree.nodes
        node_bsdf: bpy.types.Node = nodes['Principled BSDF']
        node_bsdf.inputs['Base Color'].default_value = mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], 1.0
        # TODO Specular color is unused - I will implement it if I find a need to
        node_bsdf.inputs['Specular'].default_value = 0.0
        node_bsdf.inputs['Emission'].default_value = mat.emissive_color[0], mat.emissive_color[1], mat.emissive_color[2], 1.0
        node_bsdf.inputs['Alpha'].default_value = mat.alpha

        # Vector Math - Ambient intensity
        node_ambient_intensity: bpy.types.Node = nodes.new('ShaderNodeVectorMath')
        node_ambient_intensity.name = "Ambient Intensity"
        node_ambient_intensity.location = (node_bsdf.location[0] - node_ambient_intensity.width - 50, node_bsdf.location[1])
        node_ambient_intensity.inputs['Scale'].default_value = mat.ambient_intensity

        # RGB Multiply - Vertex Color
        node_mix_vertex_color: bpy.types.Node = nodes.new('ShaderNodeMixRGB')
        node_mix_vertex_color.location = (node_ambient_intensity.location[0] - node_mix_vertex_color.width - 50, node_bsdf.location[1])
        node_mix_vertex_color.blend_type = 'MULTIPLY'
        node_mix_vertex_color.inputs['Fac'].default_value = 1.0
        node_mix_vertex_color.inputs['Color1'].default_value = (1.0, 1.0, 1.0, 1.0)
        node_mix_vertex_color.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)

        # Texture Node
        node_texture_diffuse: bpy.types.Node = nodes.new('ShaderNodeTexImage')
        node_texture_diffuse.label = mat.name  # Diffuse Texture Name
        node_texture_diffuse.width = 300
        node_texture_diffuse.location = (node_mix_vertex_color.location[0] - node_texture_diffuse.width - 50, node_bsdf.location[1])
        if mat.texture_url is not None:
            F = os.path.join(scene.directory, mat.texture_url)  # Filepath of image to add to blender
            if lilacdogoo_blender_import_wrl.debug: print(F)
            if os.path.isfile(F): node_texture_diffuse.image = bpy.data.images.load(filepath=F, check_existing=True)
        node_texture_diffuse.extension = 'REPEAT' if mat.texture_repeat else 'CLIP'

        # Vertex Color Node
        node_vertex_color: bpy.types.Node = nodes.new('ShaderNodeVertexColor')
        node_vertex_color.location = (node_mix_vertex_color.location[0] - node_vertex_color.width - 50, node_texture_diffuse.location[1] - 300)

        # Texture Alpha Node
        node_texture_alpha: bpy.types.Node = nodes.new('ShaderNodeTexImage')
        node_texture_alpha.label = "%s_Aplha" % mat.name
        node_texture_alpha.width = 300
        node_texture_alpha.location = node_texture_diffuse.location[0], node_texture_diffuse.location[1] - 500
        if mat.texture_url is not None:
            F = os.path.join(scene.directory, mat.texture_url.replace("_c.", "_a."))
            if os.path.isfile(F): node_texture_alpha.image = bpy.data.images.load(filepath=F, check_existing=True)

        # Texture Aplha Inversion Node
        node_texture_alpha_inversion: bpy.types.Node = nodes.new('ShaderNodeMath')
        node_texture_alpha_inversion.label = "Invert Alpha"
        node_texture_alpha_inversion.location = node_texture_alpha.location[0] + node_texture_alpha.width + 50, node_texture_alpha.location[1] + node_texture_alpha.height + 60
        node_texture_alpha_inversion.operation = 'SUBTRACT'
        node_texture_alpha_inversion.inputs[0].default_value = 1.0
        node_texture_alpha_inversion.inputs[1].default_value = 0.0

        # ▬ NODE LINKS ▬
        links: bpy.types.NodeLinks = blenderMaterial.node_tree.links
        links.new(node_ambient_intensity.outputs['Vector'], node_bsdf.inputs['Base Color'])
        links.new(node_mix_vertex_color.outputs['Color'], node_ambient_intensity.inputs['Vector'])
        links.new(node_texture_alpha.outputs['Color'], node_texture_alpha_inversion.inputs[1])

        # IF a texture is supplied THEN link node
        if mat.texture_url is not None:
            links.new(node_texture_diffuse.outputs['Color'], node_mix_vertex_color.inputs['Color1'])
            F = os.path.join(scene.directory, mat.texture_url.replace("_c.", "_a."))
            if os.path.isfile(F) and is_BMP_valid_transparency(F):
                links.new(node_texture_alpha.outputs['Color'], node_bsdf.inputs['Alpha'])
                blenderMaterial.blend_method = 'CLIP'
        # IF Vertext Colors are supplied THEN link node
        if mat.first_mesh_linked is not None and len(mat.first_mesh_linked.colors) > 0:
            links.new(node_vertex_color.outputs['Color'], node_mix_vertex_color.inputs['Color2'])

        blenderMaterials.append(blenderMaterial)

    for mesh in scene.meshes:
        # CREATE BLENDER STUFF
        blender_mesh: bpy.types.Mesh = bpy.data.meshes.new(mesh.name)
        blender_object: bpy.types.Object = bpy.data.objects.new(mesh.name, blender_mesh)
        blender_bMesh: bmesh.types.BMesh = bmesh.new()
        blender_bMesh.from_mesh(blender_mesh)

        # Add Data to Face Loops (UV, Color)
        blender_bMesh_uvLayer = blender_bMesh.loops.layers.uv.new() if len(mesh.texcoords) > 2 else None
        blender_bMesh_colorLayer = blender_bMesh.loops.layers.color.new() if len(mesh.colors) > 2 else None

        # Create Vertices
        blender_bMesh_verts = []  # Need to access this to create faces
        for point in mesh.points:
            blender_bMesh_verts.append(blender_bMesh.verts.new(point))
        blender_bMesh.verts.index_update()

        # Create Faces (All faces are triangles)
        for i in range(0, len(mesh.points), 3):
            # load faces backwards to correct normals direction
            blender_face_loop = [blender_bMesh_verts[i + 2], blender_bMesh_verts[i + 1], blender_bMesh_verts[i]]  # Converts to Blender format
            blender_bMesh_face: bmesh.types.BMFace = blender_bMesh.faces.new(blender_face_loop)
            # Assign UV coords - Backwards to match how the face was created (to fix normals)
            if blender_bMesh_uvLayer is not None:
                blender_bMesh_face.loops[0][blender_bMesh_uvLayer].uv = mesh.texcoords[i + 2]
                blender_bMesh_face.loops[1][blender_bMesh_uvLayer].uv = mesh.texcoords[i + 1]
                blender_bMesh_face.loops[2][blender_bMesh_uvLayer].uv = mesh.texcoords[i]
            # Assign Vertex Colors
            if blender_bMesh_colorLayer is not None:
                c = mesh.colors[i + 2]
                blender_bMesh_face.loops[0][blender_bMesh_colorLayer] = c[0], c[1], c[2], 1.0
                c = mesh.colors[i + 1]
                blender_bMesh_face.loops[1][blender_bMesh_colorLayer] = c[0], c[1], c[2], 1.0
                c = mesh.colors[i]
                blender_bMesh_face.loops[2][blender_bMesh_colorLayer] = c[0], c[1], c[2], 1.0

        # Push BMesh to Mesh
        blender_bMesh.to_mesh(blender_mesh)
        blender_mesh.materials.append(blenderMaterials[mesh.material.index])
        blender_object.color = blenderMaterials[mesh.material.index].diffuse_color
        bpy.context.scene.collection.objects.link(blender_object)
        blender_bMesh.free()


if __name__ == "__main__":
    scene = read_wrl_file("C:\\VRML", "output.wrl")
    scene = scene
