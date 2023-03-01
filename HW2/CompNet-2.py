from flask import Flask, jsonify, request, send_file
import os

app = Flask(__name__)

class Product:
    def __init__(self, id, name="", description="", picture=""):
        self.id = id
        self.name = name
        self.description = description
        self.has_picture = False
        self.picture = ""
    
    def toJsonD(self):
        return {'id' : self.id, 'name' : self.name, 'description' : self.description, 'has_picure' : self.has_picture}
    
    def clear(self):
        self.name = ""
        self.description = ""

        if self.has_picture:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], self.picture))

        self.picture = ""
        self.has_picture = False

products = []
available_ids = set()

folder_for_pictures = 'downloads'

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/product/list', methods=['GET'])
def get_product_list():
    return jsonify({'products': [products[idx].toJsonD() for idx in range(len(products)) if idx not in available_ids]}), 200

def update_ids():
    last_id = len(products)
    available_ids.update(set(range(last_id, last_id + 1000)))
    for i in range(1000):
        products.append(Product(id=last_id + i))

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    if product_id < len(products) and product_id not in available_ids:
        return jsonify(products[product_id].toJsonD())
    return "Not existing", 400

@app.route('/product/<int:product_id>/get-picture', methods=['GET'])
def get_picture(product_id):
    if product_id < len(products) and product_id not in available_ids:
        if not products[product_id].has_picture:
            return "This product doesn't have picture", 400
        path = os.path.join(app.config["UPLOAD_FOLDER"], products[product_id].picture)
        return send_file(path, as_attachment=True)
    return "Not existing", 400

@app.route('/product', methods=['POST'])
def add_product():
    if not request.json or not 'name' in request.json or not 'description' in request.json:
        return "Bad request", 400

    if len(available_ids) == 0:
        update_ids()

    product_id = -1
    for id in available_ids: # чет никак не догадалась как взять первый из сета
        product_id = id
        products[id].name = request.json['name']
        products[id].description = request.json['description']
        available_ids.remove(id)
        break
    
    return jsonify({'id' : product_id}), 201

@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if not request.json or not ('name' in request.json or 'description' in request.json):
        return "Bad request", 400
    
    if product_id >= len(products) or product_id in available_ids:
        return "Not existing", 400
    
    if 'name' in request.json:
        products[product_id].name = request.json['name']
    
    if 'description' in request.json:
        products[product_id].description = request.json['description']
    
    return "Succesfull", 200

@app.route('/product/<int:product_id>/put-picture', methods=['PUT'])
def put_picture(product_id):
    if product_id < len(products) and product_id not in available_ids:
        if 'file' in request.files and request.files['file'].filename != "":
            file = request.files['file']
            products[product_id].picture = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            products[product_id].has_picture = True
            return "Succesfull", 200
    return "Something went wrong...", 400
    

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if product_id >= len(products) or product_id in available_ids:
        return "Not existing", 400
    
    available_ids.add(product_id)
    products[product_id].clear()

    return "Succesfull", 200

if __name__ == '__main__':
    if not os.path.exists(folder_for_pictures):
        os.mkdir(folder_for_pictures)
    app.config['UPLOAD_FOLDER'] = folder_for_pictures
    app.run(debug=True)