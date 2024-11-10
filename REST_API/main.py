from flask import Flask, jsonify, request

app = Flask(__name__)

# Données simulées (une liste d'exemples)
items = [
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"},
    {"id": 3, "name": "Item 3"}
]

# Route pour obtenir tous les éléments
@app.route('/items', methods=['GET'])
def get_items():
    return jsonify({"items": items})

# Route pour obtenir un élément spécifique par son ID
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((item for item in items if item["id"] == item_id), None)
    if item:
        return jsonify(item)
    else:
        return jsonify({"message": "Item not found"}), 404

# Route pour ajouter un nouvel élément
@app.route('/items', methods=['POST'])
def add_item():
    new_item = request.get_json()  # Récupère les données JSON envoyées
    new_item["id"] = len(items) + 1  # Attribution d'un ID
    items.append(new_item)
    return jsonify(new_item), 201  # Retourne l'élément ajouté

# Route pour supprimer un élément par son ID
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global items
    items = [item for item in items if item["id"] != item_id]
    return jsonify({"message": f"Item {item_id} deleted"}), 200

# Point d'entrée principal
if __name__ == '__main__':
    app.run(debug=True)
