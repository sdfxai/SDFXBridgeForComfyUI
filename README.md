# SDFXBridgeForComfyUI - ComfyUI Custom Node for SDFX Integration

## Overview

SDFXBridgeForComfyUI is a custom node designed for seamless integration between ComfyUI and the SDFX solution. This custom node allows users to make ComfyUI compatible with SDFX when running the ComfyUI instance on their local machines.

## Dependency

Before proceeding with the installation, ensure that you have [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager) installed as a custom node. This is a mandatory dependency for the proper functioning of SDFXBridgeForComfyUI.

To install the dependency, you can use the following command:

```bash
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
cd ComfyUI-Manager && pip install -r requirements.txt
```

## Installation

1. Clone the repository into the ComfyUI custom_node directory:
    ```bash
    git clone https://github.com/sdfxai/SDFXBridgeForComfyUI.git
    ```

2. Install dependencies using pip:
    ```bash
    cd SDFXBridgeForComfyUI && pip install -r requirements.txt
    ```

## Configuration

In the sdfx node directory, you will find a sample configuration file named `sdfx.config.example.json`. Rename this file to `sdfx.config.json` and customize the paths for various modules. Here is an example configuration:

```json
{
  "args": {
    "disable-xformers": false,
    "preview-method": "taesd",
    "listen": true,
    "enable-cors-header": false,
    "port": 8188
  },

  "paths": {
    "media": {
      "gallery": "data/media/gallery",
      "input": "data/media/input",
      "output": "data/media/output",
      "workflows": "data/media/workflows",
      "templates": "data/media/templates",
      "temp": "data/media/temp"
    },

    "models": {
      "checkpoints": ["data/models/checkpoints"],
      "clip": ["data/models/clip"]
      // ... (other model paths)
    }
  }
}
```
### Path Configuration

- Each path under `paths` (e.g., `media`, `models`) represents a category of resources.
- Sub-keys (e.g., `gallery`, `checkpoints`) specify the specific resource paths.
- Paths can be relative, absolute, or omitted based on user preferences.
- If a path is relative, files will be read from the sdfx.config.json file's root.


## Usage

Users can place if they want the `sdfx.config.json` file anywhere on their computer. To make it work, ComfyUI should be launched with the `--sdfx-config-file` flag:

```bash
python main.py --sdfx-config-file=/path/to/sdfx.config.json
```
Note: All relative paths configured in `sdfx.config.json` will be relative to the location of sdfx.config.json.
## License

This project is licensed under the AGPL-3.0 license.

## Acknowledgments

Special thanks to the SDFX and ComfyUI communities for their support and collaboration.

