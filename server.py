import os
from aiohttp import web
import server
import hashlib
import folder_paths
import uuid
import time
import json
from .libs.prompt_parser import get_learned_conditioning_prompt_schedules
from .sdfx_path import get_gallery_path, get_workflows_path, get_templates_path

gallery_path = get_gallery_path()
workflows_path = get_workflows_path()
templates_path = get_templates_path()

def get_media_url_from_params(url_path, filename, type, gallery):
  return url_path + '/media?filename=' + filename + '&type=' + type + '&gallery=' + gallery

def get_dir_by_model_id_and_type(model_id, dir_type):
  # === Todo handle other media types ===
  if dir_type is None or dir_type not in ["image"]:
      dir_type = "image"

  if dir_type == "image":
      type_dir = os.path.join(gallery_path, model_id, "image")

  return type_dir, dir_type

def media_upload(post, url_path):
  image = post.get("file")
  overwrite = post.get("overwrite")
  model_id = post.get("modelId")

  image_upload_type = post.get("type")
  upload_dir, image_upload_type = get_dir_by_model_id_and_type(model_id, image_upload_type)

  if image and image.file:
    filename = image.filename
    if not filename:
      return web.Response(status=400)

    filepath = os.path.abspath(os.path.join(upload_dir, filename))

    if os.path.commonpath((upload_dir, filepath)) != upload_dir:
      return web.Response(status=400)

    if not os.path.exists(upload_dir):
      os.makedirs(upload_dir)

    split = os.path.splitext(filename)

    if overwrite is not None and (overwrite == "true" or overwrite == "1"):
      pass
    else:
      i = 1
      while os.path.exists(filepath):
        filename = f"{split[0]} ({i}){split[1]}"
        filepath = os.path.join(upload_dir, filename)
        i += 1

    with open(filepath, "wb") as f:
      f.write(image.file.read())
    return web.json_response({"name" : filename, "type": image_upload_type, "path": get_media_url_from_params(url_path, filename, image_upload_type, model_id)})
  else:
    return web.Response(status=400)

def get_domain_from_request(request):
  return request.scheme + '://' + request.host

def get_medias_from_model_id(media_id, url_path):
  media_type = 'image'
  # === Todo handle other media types ===
  media_folder = os.path.join(gallery_path, media_id, media_type)
  if os.path.exists(media_folder) and os.path.isdir(media_folder):
    return [{"name": image, "type": media_type, "path": get_media_url_from_params(url_path, image, media_type, media_id)} for image in os.listdir(media_folder)]

  return []

def add_sdfx_routes():
  # === Comfy determines the path of a checkpoint by its name ===
  # === If two different paths contain two checkpoints with the same name, there is an arbitration done to choose the appropriate path ===
  @server.PromptServer.instance.routes.get("/sdfx/model/list")
  def get_models(request):
    url_path = get_domain_from_request(request)
    models = []
    cns = folder_paths.get_filename_list('checkpoints')
    print(cns)
    for cn in cns:
        fp = folder_paths.get_full_path("checkpoints", cn)
        media_id = hashlib.md5(fp.encode()).hexdigest()
        models.append({
            "modelId": media_id,
            "name": cn,
            "type": "checkpoint",
            "gallery": get_medias_from_model_id(media_id, url_path)
        })

    return web.json_response(models)

  # === Single API to upload all kind of assets ===
  @server.PromptServer.instance.routes.post("/sdfx/media")
  async def upload_media(request):
    post = await request.post()
    url_path = get_domain_from_request(request)
    return media_upload(post, url_path)
  

  @server.PromptServer.instance.routes.get("/sdfx/media")
  async def view_media(request):
    if "filename" not in request.rel_url.query:
      return web.Response(status=400)
    if "type" not in request.rel_url.query:
      return web.Response(status=400)
    if "gallery" not in request.rel_url.query:
      return web.Response(status=400)

    filename = request.rel_url.query["filename"]
    type = request.rel_url.query["type"]
    gallery = request.rel_url.query["gallery"]

    if filename[0] == '/' or '..' in filename:
      return web.Response(status=400)
    if type[0] == '/' or '..' in type:
      return web.Response(status=400)
    if gallery[0] == '/' or '..' in gallery:
      return web.Response(status=400)

    file = os.path.join(gallery_path, gallery, type, filename)

    if os.path.isfile(file):
      if 'preview' in request.rel_url.query:
        with Image.open(file) as img:
          preview_info = request.rel_url.query['preview'].split(';')
          image_format = preview_info[0]
          if image_format not in ['webp', 'jpeg'] or 'a' in request.rel_url.query.get('channel', ''):
            image_format = 'webp'

          quality = 90
          if preview_info[-1].isdigit():
            quality = int(preview_info[-1])

          buffer = BytesIO()
          if image_format in ['jpeg'] or request.rel_url.query.get('channel', '') == 'rgb':
            img = img.convert("RGB")
          img.save(buffer, format=image_format, quality=quality)
          buffer.seek(0)

          return web.Response(body=buffer.read(), content_type=f'image/{image_format}',
                              headers={"Content-Disposition": f"filename=\"{filename}\""})

      if 'channel' not in request.rel_url.query:
        channel = 'rgba'
      else:
        channel = request.rel_url.query["channel"]

      if channel == 'rgb':
        with Image.open(file) as img:
          if img.mode == "RGBA":
            r, g, b, a = img.split()
            new_img = Image.merge('RGB', (r, g, b))
          else:
            new_img = img.convert("RGB")

          buffer = BytesIO()
          new_img.save(buffer, format='PNG')
          buffer.seek(0)

          return web.Response(body=buffer.read(), content_type='image/png', headers={"Content-Disposition": f"filename=\"{filename}\""})

      elif channel == 'a':
        with Image.open(file) as img:
          if img.mode == "RGBA":
            _, _, _, a = img.split()
          else:
            a = Image.new('L', img.size, 255)

          # alpha img
          alpha_img = Image.new('RGBA', img.size)
          alpha_img.putalpha(a)
          alpha_buffer = BytesIO()
          alpha_img.save(alpha_buffer, format='PNG')
          alpha_buffer.seek(0)

          return web.Response(body=alpha_buffer.read(), content_type='image/png', headers={"Content-Disposition": f"filename=\"{filename}\""})
      else:
        return web.FileResponse(file, headers={"Content-Disposition": f"filename=\"{filename}\""})

    return web.Response(status=400)

  @server.PromptServer.instance.routes.get("/sdfx/prompt_parser")
  async def prompt_parser(request):
    if "prompt" in request.rel_url.query:
      prompt = request.rel_url.query["prompt"]
      env = request.rel_url.query['env'] if 'env' in request.rel_url.query else 'prod'
      g = lambda p: get_learned_conditioning_prompt_schedules([p], env)[0]
      return web.json_response({'prompt' : prompt, 'data' : g(prompt)})
    return web.Response(status=404)
  
  @server.PromptServer.instance.routes.get("/sdfx/workflow/list")
  @server.PromptServer.instance.routes.get("/sdfx/template/list")
  async def workflows_templates(request):
    list = []
    path = request.url.path

    if path == "/sdfx/workflow/list":
      working_dir = workflows_path
    elif path == "/sdfx/template/list":
      working_dir = templates_path
    
    for filename in os.listdir(working_dir):
      if filename.endswith(".json"):
        file_path = os.path.join(working_dir, filename)
        with open(file_path, 'r') as file:
          try:
            data = json.load(file)
            uid = data.get('uid')
            name = data.get('name')
            dateCreated = data.get('dateCreated')
            metas = data.get('metas')
            list.append({ 'uid': uid, 'name': name, 'metas': metas, 'dateCreated': dateCreated})

          except json.JSONDecodeError as e:
            return web.json_response({'error': 'invalid Json'}, status=400)
    return web.json_response(list)

  @server.PromptServer.instance.routes.get("/sdfx/workflow")
  @server.PromptServer.instance.routes.post("/sdfx/workflow")
  @server.PromptServer.instance.routes.put("/sdfx/workflow")
  @server.PromptServer.instance.routes.delete("/sdfx/workflow")
  @server.PromptServer.instance.routes.get("/sdfx/template")
  @server.PromptServer.instance.routes.post("/sdfx/template")
  @server.PromptServer.instance.routes.put("/sdfx/template")
  @server.PromptServer.instance.routes.delete("/sdfx/template")
  async def workflow_template(request):
    method = request.method
    path = request.url.path
    if method == 'GET':
      uid = request.query.get('uid')
      if not uid:
        return web.json_response({'error': 'uid missing'}, status=400)
      if path == "/sdfx/workflow":
        filename = os.path.join(workflows_path, f"{uid}.json")
      elif path == "/sdfx/template":
        filename = os.path.join(templates_path, f"{uid}.json")
      if not os.path.isfile(filename):
        return web.json_response({'error': 'file missing'}, status=404)
      with open(filename, 'r') as file:
        file_content = json.load(file)
      return web.json_response(file_content)
    elif method == 'POST' or method == 'PUT':
      try:
        data = await request.json()
        data['dateCreated'] = int(time.time())
        if(method == 'POST'):
          hash = str(uuid.uuid4())
        else:
          hash = request.query.get('uid')
          if not hash:
            return web.json_response({'error': 'uid missing'}, status=400)
        data['uid'] = hash
        if path == "/sdfx/workflow":
          filename = os.path.join(workflows_path, f"{hash}.json")
        elif path == "/sdfx/template":
          filename = os.path.join(templates_path, f"{hash}.json")
        with open(filename, 'w') as file:
          json.dump(data, file)
        response = {'uid': data.get('uid'), 'name': data.get('name'), 'metas': data.get('meta'), 'dateCreated': data.get('dateCreated')}
        return web.json_response(response)
      except json.JSONDecodeError:
        return web.json_response({'error': 'invalid Json'}, status=400)
    elif method == 'DELETE':
      uid = request.query.get('uid')
      if not uid:
        return web.json_response({'error': "Fatal: Parameter 'uid' missing"}, status=400)
      if path == "/sdfx/workflow":
        filename = os.path.join(workflows_path, f"{uid}.json")
      elif path == "/sdfx/template":
        filename = os.path.join(templates_path, f"{uid}.json")
      if os.path.isfile(filename):
        os.remove(filename)
      return web.json_response({'uid': uid, 'status':'deleted'})
    else:
      return web.Response(status=404)
    

  @server.PromptServer.instance.routes.get("/sdfx/input")
  @server.PromptServer.instance.routes.delete("/sdfx/input")
  @server.PromptServer.instance.routes.get("/sdfx/output")
  @server.PromptServer.instance.routes.delete("/sdfx/output")
  async def input_output(request):
    method = request.method
    path = request.url.path
    if method == 'GET':
      name = request.query.get('name')
      if not name:
        return web.json_response({'error': 'name missing'}, status=400)
      if path == '/sdfx/input':
        filename = os.path.join(folder_paths.get_input_directory(), name)
      elif path == '/sdfx/output':
        filename = os.path.join(folder_paths.get_output_directory(), name)
      if not os.path.isfile(filename):
        return web.json_response({'error': 'file missing'}, status=404)
      return web.json_response({'name': name})
    if method == 'DELETE':
      name = request.query.get('name')
      if not name:
        return web.json_response({'error': 'name missing'}, status=400)
      if path == '/sdfx/input':
        filename = os.path.join(folder_paths.get_input_directory(), name)
      elif path == '/sdfx/output':
        filename = os.path.join(folder_paths.get_output_directory(), name)
      if os.path.isfile(filename):
        os.remove(filename)
      return web.json_response({'name': name, 'status':'deleted'})
    
  @server.PromptServer.instance.routes.get("/sdfx/input/list")
  @server.PromptServer.instance.routes.get("/sdfx/output/list")
  async def inputs_outputs(request):
    list = []
    path = request.url.path

    if path == '/sdfx/input/list':
      working_dir = folder_paths.get_input_directory()
    elif path == '/sdfx/output/list':
      working_dir = folder_paths.get_output_directory()

    for filename in os.listdir(working_dir):
      if '.' in filename:
        list.append({'name': filename})
    return web.json_response(list)