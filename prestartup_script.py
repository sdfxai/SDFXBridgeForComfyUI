import argparse

# Hack to pass extra args to main.py 
def parse_args_override(self, args=None, namespace=None):
    namespace, _ = self.parse_known_args(args, namespace)
    return namespace

argparse.ArgumentParser.parse_args = parse_args_override 

parser = argparse.ArgumentParser()
parser.add_argument("--sdfx-config-file", type=str, default=None, help="Path for sdfx config file")
args = parser.parse_args()

#args.sdfx_config_file
