import os
import json
import folder_paths
from .prestartup_script import args

sdfx_config_file_name = 'sdfx.config.json'

#=== Best effort to find sdfx_config_file_path ===
def find_sdfx_config_path():
  if args.sdfx_config_file is not None:
    if os.path.exists(args.sdfx_config_file):
      return args.sdfx_config_file
  path = os.path.abspath(os.path.dirname(__file__))
  config_path_found = None
  try:
    for _ in range(6):
      config_path = os.path.join(path, sdfx_config_file_name)
      if os.path.exists(config_path):
        config_path_found = config_path
      path = os.path.dirname(path)
  except Exception as e:
    print(f"Error File access : {e}")
  if config_path_found is not None:
    return config_path_found
  raise FileNotFoundError()

#=== if path is relative return absolute ===
def get_sdfx_absolute_path(path):
  if path is None:
    return None
  elif os.path.isabs(path):
    return path
  else:
    sdfx_config_path
    try:
      sdfx_config_path = find_sdfx_config_path()
    except FileNotFoundError:
      sdfx_config_path = os.path.abspath(os.path.dirname(__file__))
    parent_path = os.path.dirname(find_sdfx_config_path())
    return os.path.join(parent_path, path)

isPathFound = True
try:
  gallery_path = get_sdfx_absolute_path('data/media/gallery')
  workflows_path = get_sdfx_absolute_path('data/media/worflows')
  templates_path = get_sdfx_absolute_path('data/media/gallery')
except FileNotFoundError:
  isPathFound = False

#=== add all sdfx path to comfy folder_paths ===
def load_sdfx_extra_path_config():
  global gallery_path, workflows_path, templates_path
  try:
    sdfx_config_file = find_sdfx_config_path()
    with open(sdfx_config_file, 'r') as json_file:
      data = json.load(json_file)

      #=== load sdfx models ===
      models = data.get('paths', {}).get('models', None)
      if isinstance(models, dict):
        for m in models:
          for x in models[m]:
            full_path = get_sdfx_absolute_path(x)
            print("Adding sdfx extra search path", m, full_path)
            folder_paths.add_model_folder_path(m, full_path)
      
      #=== load sdfx medias ===
      media = data.get('paths', {}).get('media', {})
      o = media.get('output', None)
      if isinstance(o, str):
        output_dir = get_sdfx_absolute_path(o)
        print("Setting sdfx output path", output_dir)
        folder_paths.set_output_directory(output_dir)

      i = media.get('input', None)
      if isinstance(i, str):
        input_dir = get_sdfx_absolute_path(i)
        print("Setting sdfx input path", input_dir)
        folder_paths.set_input_directory(input_dir)

      t = media.get('temp', None)
      if isinstance(t, str):
        temp_dir = get_sdfx_absolute_path(t)
        print("Setting sdfx temp path", temp_dir)
        folder_paths.set_temp_directory(temp_dir)

      g = media.get('gallery', None)
      if isinstance(g, str):
        gallery_path = get_sdfx_absolute_path(g)
        print("Setting sdfx gallery path", gallery_path)

      w = media.get('workflows', None)
      if isinstance(w, str):
        workflows_path = get_sdfx_absolute_path(w)
        print("Setting sdfx workflows path", workflows_path)

      te = media.get('templates', None)
      if isinstance(te, str):
        templates_path = get_sdfx_absolute_path(te)
        print("Setting sdfx templates path", templates_path)

  except json.JSONDecodeError as e:
    print(f"[SdfxForComfyUI] FATAL -> {sdfx_config_file_name} is not valid, it will not be loaded !")
  except FileNotFoundError:
    print(f"[SdfxForComfyUI] FATAL -> {sdfx_config_file_name} not found and not specified")
  except Exception as e:
    print(f"[SdfxForComfyUI] FATAL -> : {e}")

def get_gallery_path():
  return None if not isPathFound else gallery_path

def get_workflows_path():
  return None if not isPathFound else workflows_path

def get_templates_path():
  return None if not isPathFound else templates_path