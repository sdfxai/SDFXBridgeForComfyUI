import argparse
import os
import sys
import json

# Hack to pass extra args to main.py 
def parse_args_override(self, args=None, namespace=None):
    namespace, _ = self.parse_known_args(args, namespace)
    return namespace

argparse.ArgumentParser.parse_args = parse_args_override 

parser = argparse.ArgumentParser()
parser.add_argument("--sdfx-config-file", type=str, default=None, help="Path for sdfx config file")
args = parser.parse_args()

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

def load_boot_config():
  try:
    sdfx_config_file = find_sdfx_config_path()
    with open(sdfx_config_file, 'r') as json_file:
      data = json.load(json_file)
      #=== load port from config file ===
      port = data.get('args', {}).get('port', None)
      if isinstance(port, int):
        sys.argv.append("--port=" + str(port))
      #=== load listen from config file ===
      listen = data.get('args', {}).get('listen', None)
      if isinstance(listen, str):
        sys.argv.append("--listen=" + listen)
      #=== load disable-xformers from config file ===
      dx = data.get('args', {}).get('disable-xformers', None)
      if isinstance(dx, bool) and dx == True:
        sys.argv.append("--disable-xformers")
      #=== load preview-method from config file ===
      pm = data.get('args', {}).get('preview-method', None)
      if isinstance(pm, str):
        sys.argv.append("--preview-method=" + pm)
      #=== load enable-cors-header from config file ===
      ch = data.get('args', {}).get('enable-cors-header', None)
      if isinstance(ch, bool) and ch == True:
        sys.argv.append("--enable-cors-header")

  except json.JSONDecodeError as e:
    print(f"[SDFXBridgeForComfyUI] FATAL -> {sdfx_config_file_name} is not valid, it will not be loaded !")
  except FileNotFoundError:
    print(f"[SDFXBridgeForComfyUI] FATAL -> {sdfx_config_file_name} not found and not specified")
  except Exception as e:
    print(f"[SDFXBridgeForComfyUI] FATAL -> : {e}")

load_boot_config()