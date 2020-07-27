import bpy
import datetime

from .. import updater, updater_ops
from ..core import animations
from ..core import recorder as recorder_manager
from ..core import receiver as receiver_cls
from ..core.icon_manager import Icons
from ..operators import receiver, recorder

row_scale = 0.75
paired_inputs = {}


is_moved = True


def separator(layout, scale=1):
    # Add small separator
    row = layout.row(align=True)
    row.scale_y = scale
    row.label(text='')


# Initializes the Rokoko panel in the toolbar
class ToolPanel:
    if not is_moved:
        bl_label = 'Rokoko'
        bl_idname = 'VIEW3D_TS_rokoko'
        bl_category = 'Rokoko'
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
    else:
        bl_category = "Tools"
        bl_space_type = 'PROPERTIES'
        bl_region_type = 'WINDOW'
        bl_context = "object"


class RokokoMainPanel(ToolPanel, bpy.types.Panel):
    bl_idname = "OBJECT_PT_rokoko_main"
    bl_label = "Rokoko"

    def draw(self, context):
        pass


# Main panel of the Rokoko panel
class ReceiverPanel(ToolPanel, bpy.types.Panel):
    bl_label = 'Rokoko Studio Live'
    bl_idname = 'VIEW3D_PT_rsl_receiver_v2'
    if is_moved:
        bl_parent_id = "OBJECT_PT_rokoko_main"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        # box = layout.box()
        updater.check_for_update_background(check_on_startup=True)
        updater_ops.draw_update_notification_panel(layout)

        col = layout.column()

        row = col.row(align=True)
        row.label(text='Port:')
        row.enabled = not receiver.receiver_enabled
        row.prop(context.scene, 'rsl_receiver_port', text='')

        # row = col.row(align=True)
        # row.label(text='FPS:')
        # row.enabled = not receiver.receiver_enabled
        # row.prop(context.scene, 'rsl_receiver_fps', text='')

        row = col.row(align=True)
        row.label(text='Scene Scale:')
        row.prop(context.scene, 'rsl_scene_scaling', text='')

        layout.separator()

        row = layout.row(align=True)
        row.prop(context.scene, 'rsl_reset_scene_on_stop')

        row = layout.row(align=True)
        row.prop(context.scene, 'rsl_hide_mesh_during_play')

        row = layout.row(align=True)
        row.scale_y = 1.3
        if receiver.receiver_enabled:
            row.operator(receiver.ReceiverStop.bl_idname, icon='PAUSE', depress=True)
        else:
            row.operator(receiver.ReceiverStart.bl_idname, icon='PLAY')

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.enabled = receiver.receiver_enabled
        if not context.scene.rsl_recording:
            row.operator(recorder.RecorderStart.bl_idname, icon_value=Icons.START_RECORDING.get_icon())
        else:
            row.operator(recorder.RecorderStop.bl_idname, icon='SNAP_FACE', depress=True)
            timestamps = list(recorder_manager.recorded_timestamps.keys())
            if not timestamps:
                return

            time_recorded = int(timestamps[-1] - timestamps[0])
            row = layout.row(align=True)
            row.label(text='Recording time: ' + str(datetime.timedelta(seconds=time_recorded)))

        if receiver.receiver_enabled and receiver_cls.show_error:
            for i, error in enumerate(receiver_cls.show_error):
                if i == 0:
                    row = layout.row(align=True)
                    row.label(text=error, icon='ERROR')
                else:
                    row = layout.row(align=True)
                    row.scale_y = 0.3
                    row.label(text=error, icon='BLANK1')
            return

        # Show all inputs
        global paired_inputs
        paired_inputs = {}
        used_trackers = []
        used_faces = []

        # Get all paired inputs. Paired inputs are paired to an object in the scene
        for obj in bpy.data.objects:
            # Get paired props and trackers
            if animations.props or animations.trackers:
                if obj.rsl_animations_props_trackers and obj.rsl_animations_props_trackers != 'None':
                    paired = paired_inputs.get(obj.rsl_animations_props_trackers.split('|')[1])
                    if not paired:
                        paired_inputs[obj.rsl_animations_props_trackers.split('|')[1]] = [obj.name]
                    else:
                        paired.append(obj.name)

            # Get paired faces
            if animations.faces and obj.rsl_animations_faces and obj.rsl_animations_faces != 'None':
                paired = paired_inputs.get(obj.rsl_animations_faces)
                if not paired:
                    paired_inputs[obj.rsl_animations_faces] = [obj.name]
                else:
                    paired.append(obj.name)

            # Get paired actors
            if animations.actors and obj.rsl_animations_actors and obj.rsl_animations_actors != 'None':
                paired = paired_inputs.get(obj.rsl_animations_actors)
                if not paired:
                    paired_inputs[obj.rsl_animations_actors] = [obj.name]
                else:
                    paired.append(obj.name)

            # Get paired actors
            if animations.gloves and obj.rsl_animations_gloves and obj.rsl_animations_gloves != 'None':
                paired = paired_inputs.get(obj.rsl_animations_gloves)
                if not paired:
                    paired_inputs[obj.rsl_animations_gloves] = [obj.name]
                else:
                    paired.append(obj.name)

        # This is used as a small spacer
        row = layout.row(align=True)
        row.scale_y = 0.01
        row.label(text=' ')

        # Display all paired and unpaired inputs
        for actor in animations.actors:
            if actor['profileName']:
                row = layout.row(align=True)
                row.scale_y = row_scale
                row.label(text=actor['profileName'], icon='ANTIALIASED')

                split = layout.row(align=True)
                split.scale_y = row_scale
                add_indent(split)
                show_actor(split, actor)

                for tracker in animations.trackers:
                    if tracker['connectionId'] == actor['id']:
                        split = layout.row(align=True)
                        split.scale_y = row_scale
                        add_indent(split, empty=True)
                        add_indent(split)
                        show_tracker(split, tracker)
                        used_trackers.append(tracker['name'])

                for face in animations.faces:
                    if face.get('profileName') and face.get('profileName') == actor['profileName']:
                        split = layout.row(align=True)
                        split.scale_y = row_scale
                        add_indent(split)
                        show_face(split, face)
                        used_faces.append(face['faceId'])

                # split = layout.row(align=True)
                # add_indent(split)
                # row = split.row(align=True)
                # row.label(text='faceId', icon_value=Icons.FACE.get_icon())

        for prop in animations.props:
            show_prop(layout, prop, scale=True)

            for tracker in animations.trackers:
                if tracker['connectionId'] == prop['id']:
                    split = layout.row(align=True)
                    split.scale_y = row_scale
                    add_indent(split)
                    show_tracker(split, tracker)
                    used_trackers.append(tracker['name'])

        for tracker in animations.trackers:
            if tracker['name'] not in used_trackers:
                show_tracker(layout, tracker, scale=True)

        # row = layout.row(align=True)
        # row.label(text='5', icon_value=Icons.VP.get_icon())

        for face in animations.faces:
            if face['faceId'] not in used_faces:
                show_face(layout, face, scale=True)

        # row = layout.row(align=True)
        # row.label(text='faceId2', icon_value=Icons.FACE.get_icon())

        for glove in animations.gloves:
            show_glove(layout, glove, scale=True)


def add_indent(split, empty=False):
    row = split.row(align=True)
    row.alignment = 'LEFT'
    if empty:
        row.label(text="", icon='BLANK1')
    else:
        row.label(text="", icon_value=Icons.PAIRED.get_icon())


def show_actor(layout, actor, scale=False):
    row = layout.row(align=True)
    if scale:
        row.scale_y = row_scale

    if paired_inputs.get(actor['id']):
        row.label(text=actor['name'] + '  --> ' + ', '.join(paired_inputs.get(actor['id'])), icon_value=Icons.SUIT.get_icon())
    else:
        row.enabled = False
        row.label(text=actor['name'], icon_value=Icons.SUIT.get_icon())


def show_glove(layout, glove, scale=False):
    row = layout.row(align=True)
    if scale:
        row.scale_y = row_scale

    if paired_inputs.get(glove['gloveID']):
        row.label(text=glove['gloveID'] + '  --> ' + ', '.join(paired_inputs.get(glove['gloveID'])), icon='VIEW_PAN')
    else:
        row.enabled = False
        row.label(text=glove['gloveID'], icon='VIEW_PAN')


def show_face(layout, face, scale=False):
    row = layout.row(align=True)
    if scale:
        row.scale_y = row_scale

    if paired_inputs.get(face['faceId']):
        row.label(text=face['faceId'] + '  --> ' + ', '.join(paired_inputs.get(face['faceId'])), icon_value=Icons.FACE.get_icon())
    else:
        row.enabled = False
        row.label(text=face['faceId'], icon_value=Icons.FACE.get_icon())


def show_tracker(layout, tracker, scale=False):
    row = layout.row(align=True)
    if scale:
        row.scale_y = row_scale

    if paired_inputs.get(tracker['name']):
        row.label(text=tracker['name'] + '  --> ' + ', '.join(paired_inputs.get(tracker['name'])), icon_value=Icons.VP.get_icon())
    else:
        row.enabled = False
        row.label(text=tracker['name'], icon_value=Icons.VP.get_icon())


def show_prop(layout, prop, scale=False):
    row = layout.row(align=True)
    if scale:
        row.scale_y = row_scale

    if paired_inputs.get(prop['id']):
        row.label(text=prop['name'] + '  --> ' + ', '.join(paired_inputs.get(prop['id'])), icon='FILE_3D')
    else:
        row.enabled = False
        row.label(text=prop['name'], icon='FILE_3D')
