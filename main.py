import dis
import os
import pathlib
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import base64
from io import BytesIO 
import PIL
import numpy as np
import tensorflow.lite as lite
#import tflite_runtime.interpreter as lite 

#model_path = pathlib.Path("/static/model.tflite")


    

model = lite.Interpreter("static/model.tflite")
model.allocate_tensors()

input_details = model.get_input_details()
output_details = model.get_output_details()

class_mapping = {
    0:'Building',
    1:'Forest',
    2:'Glacier',
    3:'Mountain',
    4:'Sea',
    5:'Street'
}

def model_predict(images_arr):
    predictions = [0] * len(images_arr)
    
    for i, val in enumerate(predictions):
        model.set_tensor(input_details[0]['index'], images_arr[i].reshape((1,150,150,3)))
        model.invoke()
        predictions[i] = model.get_tensor(output_details[0]['index']).reshape((6,))
        
    prediction_probabilities = np.array(predictions)
    argmaxs = np.argmax(prediction_probabilities, axis=1)
    
    return argmaxs

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.post('/uploadfiles', response_class=HTMLResponse)
async def create_upload_files(files: List[UploadFile] = File(...)):
    images = []

    for file in files:
        f = await file.read()
        images.append(f)
    
    
    
    images = [PIL.Image.open(BytesIO(img)) for img in images]
    images_resized = [img.resize((150,150)) for img in images]
    images_rgb = [np.asarray(img) for img in images_resized]

    names = [file.filename for file in files]

    for image, name in zip(images_rgb, names):
        pillow_image = PIL.Image.fromarray(image)
        pillow_image.save('static/'+name)

    images_paths = ['static/' + name for name in names]

    images_arr = np.array(images_rgb, dtype=np.float32)
    class_indexes = model_predict(images_arr)

    class_prediction = [class_mapping[x] for x in class_indexes]

    column_labels = ["Images", "Prediction"]

    table_html = get_html_table(images_paths, class_prediction, column_labels)
    return head_html + table_html

@app.get("/", response_class=HTMLResponse)
async def main():
    content = head_html+"""
    <marquee width="525" behaviour="alternate"><h1 style="color:red;font-family:Arial">Please Upload Your Scene!</h1></marquee>
    <h2><b>ml application for scene recognition</b></h2>
    <h3 style="font-family:Arial">We'll Try to predict which of these catgories they are:</h3><br>
    """
    
    original_paths = ['forest_1.jpg', 'glacier_1.jpg', 'mountain_1.jpg', 'sea_1.jpg', 'street_1.jpg']
    

    full_original_paths = ['static/original/'+x for x in original_paths]

    
    display_names = ["Building", "Forest", "Glacier", "Mountain", "Sea", "Street"]

    
    column_label = ["Image", "Labels"]
    content = content + get_html_table(full_original_paths, display_names, column_label)
    
    content = content + """
    <br/>
    <br/>
    <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
    <input name="files" type="file" multiple>
    <input type="submit">
    </form>
    </body>
    """

    return content

head_html = """
<head>
    <meta name = "viewport" content="width=device-width, initial-scale=1"/>
</head>
<body style="background-color:powderblue;">
<center>
"""

def get_html_table(image_paths, names, column_labels):
    s = '<table allign = "center">'
    if column_labels:
        s += '<tr><th><h4 style="font-family:Arial">'+column_labels[0]+'</h4></th><th><h4 style="font-family:Arial">'+column_labels[1]+'</h4></th><th>'

    for name, image_path in zip(names, image_paths):

        s += f'<tr><td><img height="100" src="/{image_path}"></td>'
        s += '<td style="text-align:center"><b>'+ name + '</b></td></tr>'
    s += '</table>'


    return s

