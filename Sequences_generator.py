import bpy
import math
import itertools
import os


# Set render engine and adjust render parameters
def config_render(engine='cycles', device='GPU', samples=32, use_denoising=False, resolution_x=1920, resolution_y=1080):
    
    # Set image resolution and fps
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    
    # Adjust cycles render engine parameters
    if engine=='cycles':
        bpy.context.scene.render.engine = 'CYCLES'
        scene = bpy.context.scene.cycles    
        scene.feature_set = 'EXPERIMENTAL'
        scene.device = device
        scene.samples = samples         # Number of samples to render for each pixel
        scene.use_denoising = use_denoising
        scene.dicing_rate = 2          # Size of micropolygon in pixels
        scene.offscreen_dicing_scale = 10          # Multiplier for dicing rate of geometry outside of the camera view
        scene.max_subdivisions = 12
    
    # Adjust eevee render engine parameters
    elif engine=='eevee':
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        scene = bpy.context.scene.eevee
        bpy.context.scene.eevee.taa_render_samples = samples          # Number of samples to render for each pixel
        
    else:
        print ('please write a valid render engine')
        

# Unlink native sky, link HDRI to background node and set its strength
def config_hdri(name, strength=0.5, path='//HDRI/'):
    
    # Get the environment node tree of the current scene
    env_texture = bpy.data.worlds["World"].node_tree.nodes['Environment Texture']
    
    # Load HDRI and adjust its strength
    hdri_dir = path + name + '.hdr'
    env_texture.image = bpy.data.images.load(hdri_dir)
    
    # Link HDRI node to background node and adjust strength
    links = bpy.context.scene.world.node_tree.links
    links.new(env_texture.outputs[0], bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0])
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = strength
    
    # Adjust a specific hdri
    if name == 'Coast':
        bpy.data.worlds["World"].node_tree.nodes["Mapping"].inputs[1].default_value[2] = 0.07

    

# Unlink HDRI image and scene background, link a preset sky texture and adjust sunlight
def config_sunlight(sky_name, strength=0.5, turbidity=2, ground_albedo=0.2, sun_intensity=1, sun_elevation=0.26,
sun_disc=True, altitude=0, air_density=1, dust_density=1, ozone_density=1):
    
    sky_texture = bpy.data.worlds["World"].node_tree.nodes["Sky Texture"]
    
    # Adjust sky texture parameters
    if sky_name=='preetham':
        sky_texture.sky_type = 'PREETHAM'
        sky_texture.turbidity = trubidity
    elif sky_name=='hosek':
        sky_texture.sky_type = 'HOSEK_WILKIE'
        sky_texture.turbidity = trubidity
        sky_texture.ground_albedo = ground_albedo
    elif sky_name=='nishita':
        sky_texture.sky_type = 'NISHITA'
        sky_texture.sun_disc = sun_disc
        sky_texture.sun_intensity = sun_intensity
        sky_texture.sun_elevation = sun_elevation
        sky_texture.altitude = altitude
        sky_texture.air_density = air_density
        sky_texture.dust_density = dust_density
        sky_texture.ozone_density = ozone_density
    else:
        print('please write a valid sky texture')
    
    # Link sky texture node to background node and adjust strength
    links = bpy.context.scene.world.node_tree.links
    links.new(sky_texture.outputs[0], bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0])
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = strength


# Adjust fog parameters
def config_fog(intensity, start_distance=5, max_distance=5000, evolution_type='quadratic'):
    
    bpy.data.scenes["Scene"].node_tree.nodes["Mix"].inputs[0].default_value = intensity
    bpy.context.scene.world.mist_settings.start = start_distance
    bpy.context.scene.world.mist_settings.depth = max_distance
    bpy.context.scene.world.mist_settings.falloff = evolution_type.upper()
    
    
# Disable a certain object in renders
def hide_object(name, hide, collection=False):
    
    if collection==True:
        bpy.data.collections[name].hide_render = hide
    else:
        bpy.data.objects[name].hide_render = hide


# Edit one ocean texture, bake a new sequence and import those frames to the ocean 
def config_ocean(ocean_number, total_frames, type, color='no_color', resolution=20, random_seed=0, wave_scale=2, wave_scale_min=0, choppiness=1.5, wind_velocity=7, wave_alignment=0.75, wave_direction=0, damping=0.5, 
use_foam=False, foam_coverage=0.2):
        
    which_ocean = 'OceanPreview' + str(ocean_number)
    ocean = bpy.data.objects[which_ocean].modifiers["Ocean"]
    
    # Adjust ocean type
    if type == 'turbulent':
        ocean.spectrum = 'PHILLIPS'
    elif type == 'established':
        ocean.spectrum = 'PIERSON_MOSKOWITZ'
    elif type == 'established_sharp_peaks':
        ocean.spectrum = 'JONSWAP'
    elif type == 'shallow':
        ocean.spectrum = 'TEXEL_MARSEN_ARSLOE'
    else:
        print('please write a valid ocean type')
         
    # Adjust the properties of one ocean texture
    ocean.resolution = resolution
    ocean.random_seed = random_seed          # Seed of the random generator
    ocean.wave_scale = wave_scale          # Scale of the displacement effect   
    ocean.wave_scale_min = wave_scale_min          # Shortest allowed wavelength
    ocean.choppiness = choppiness          # Scale of the wave's crest
    ocean.wind_velocity = wind_velocity          # Wind speed in m/s
    ocean.wave_alignment = wave_alignment          # How much the waves are aligned to each other
    ocean.wave_direction = wave_direction          # Main direction of the waves when they are (partially) aligned, in rads
    ocean.damping = damping          # Damp reflected waves going on opposite direction to the wind
    ocean.use_foam = use_foam          # Generate foam mask as a vertex color channel
    if ocean.use_foam == True:
        ocean.foam_layer_name = "foam"
        ocean.foam_coverage = foam_coverage          # Amount of generated foam 
    
    # Deselect any selected object
    for obj in bpy.data.objects:
        if obj.select_get() == True:
            obj.select_set(False)
    
    # Bake an image sequence according to the ocean texture defined
    bpy.data.objects[which_ocean].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[which_ocean]
    bpy.ops.object.ocean_bake(modifier="Ocean")
    
    # Load those sequences previously baked
    sequence_dir = "//OceanD" + str(ocean_number) + "_test/disp_0001.exr"
    bpy.data.materials["Ocean"].node_tree.nodes["Image Texture"].image = bpy.data.images.load(sequence_dir, check_existing = True)
    bpy.data.images["disp_0001.exr"].source = 'SEQUENCE'
    bpy.data.materials["Ocean"].node_tree.nodes["Image Texture"].image_user.frame_start = 1
    bpy.data.materials["Ocean"].node_tree.nodes["Image Texture"].image_user.frame_duration = total_frames


# Set ocean color
def config_ocean_color(color='no_color'):
    
    color_code = bpy.data.materials["Ocean"].node_tree.nodes["Principled BSDF"].inputs[0]
    if color == 'no_color':
        color_code.default_value = (0, 0, 0, 1)
    elif color == 'deft_blue':
        color_code.default_value = (0.0212847, 0.048292, 0.193216, 1)
    elif color == 'aquamarine':
        color_code.default_value = (0.21223, 1, 0.658375, 1)
    else:
        print('please write a valid color name')
        

# Establish a camera position and rotation for a given frame
def insert_keyframe(keyframe, key_location, key_rotation):
    
    # Define camera settings
    camera = bpy.context.scene.objects['Camera']
    camera.location = key_location
    camera.rotation_euler = key_rotation          # Rotation in rads
    
    # Insert keyframe
    camera.keyframe_insert(data_path="location", frame=keyframe)
    camera.keyframe_insert(data_path="rotation_euler", frame=keyframe)
    

# Delete keyframes
def delete_keyframe(frame_list='all'):
    
    camera = bpy.context.scene.objects['Camera']
    
    # Delete all keyframes or just the selected ones
    if frame_list=='all':
        for frame_number in range(0, 251):          # todo alterar 
            camera.keyframe_delete(data_path='location', frame=frame_number)
            camera.keyframe_delete(data_path='rotation_euler', frame=frame_number)
    else:
        for frame_number in frame_list:
            camera.keyframe_delete(data_path='location', frame=frame_number)
            camera.keyframe_delete(data_path='rotation_euler', frame=frame_number)
            

def set_orbit(camera_dist, camera_height, total_frames=250):
    
    # Estimate camera position and rotation on frame 1
    camera_positions = [(camera_dist, 0, camera_height)]
    camera_rotations = [(math.atan(camera_dist / camera_height), 0, math.pi/2)]
    
    # Delete all keyframes and insert first keyframe
    delete_keyframe()
    insert_keyframe(1, camera_positions[0], camera_rotations[0])
    
    total_keyframes = 5
    step = total_frames/(total_keyframes-1)
    angle_step = (2 * math.pi)/(total_keyframes - 1)
    
    # Estimate other positions and rotations
    for i in range(1, total_keyframes):
        last_position = camera_positions[-1]
        last_rotation = camera_rotations[-1]
        next_position = (camera_dist * math.cos(i * angle_step), camera_dist * math.sin(i * angle_step), last_position[2])
        next_rotation = (last_rotation[0], last_rotation[1], last_rotation[2] + angle_step)
        camera_positions.append(next_position)
        camera_rotations.append(next_rotation)
        
        # Insert keyframes
        insert_keyframe(i * step, next_position, next_rotation)
        

# Render the defined sequence
def render(images_dir, segmentations_dir, sequence=True, frame_start=1, frame_end=250, frame_step=1):
    
    # Set frames parameters
    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    bpy.context.scene.frame_step = frame_step          # Number of frames to skip forward while rendering
    
    # Set output directory
    bpy.data.scenes["Scene"].node_tree.nodes["File Output"].base_path = images_dir  
    bpy.data.scenes["Scene"].node_tree.nodes["File Output.001"].base_path = segmentations_dir
    
    # Render the images while display the process on a new window 
    #bpy.ops.render.opengl('INVOKE_DEFAULT')
    bpy.ops.render.render(animation=sequence, write_still=True)
    



sequence_frames = 250
image_resolution_x = 1920
image_resolution_y = 1080
render_engine = 'cycles'
pixel_samples = 64

output_dir = '/mnt/hdd_2tb_1/fsmatilde/Dataset_Blender/Dataset/test_script2/'

variables = ['Sky types', 'Sky strength', 'Wave scale', 'Choppiness']
sky_types = ['Coast', 'CAVOK', 'BKN', 'OVC'] 
sky_strength = [0.3, 0.65, 1]
wave_scales = [0.7,1.8,3.5]
choppiness_values = [0.7, 1.50, 2.30]


combinations = list(itertools.product(sky_types, sky_strength, wave_scales, choppiness_values))

config_render(engine=render_engine, samples=pixel_samples, resolution_x=image_resolution_x, resolution_y=image_resolution_y)

sequence_number = 1

for i in range(0, len(combinations)):
    config_hdri(combinations[i][0], strength=combinations[i][1])
    config_ocean(1, sequence_frames, 'turbulent', wave_scale=combinations[i][2], choppiness=combinations[i][3])
    sequence_name = 'Sequence.' + format(sequence_number, "04")
    sequence_dir = output_dir + sequence_name
    txt_name = "Config."+format(sequence_number, "04")+".txt"
    render(sequence_dir, sequence_dir, sequence=True, frame_step=100)
    with open(os.path.join(sequence_dir, txt_name), '+w') as txt_file:
        for n in range(0, len(variables)):
            txt_file.write(variables[n] + ' = ' + str(combinations[i][n]))
            txt_file.write('\n')
    txt_file.close()
    sequence_number += 1
    
               
