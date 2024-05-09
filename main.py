from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy.orm import relationship
from flask_marshmallow import Marshmallow

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:root@localhost/main"
app.config['JWT_SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)
ma = Marshmallow(app)

# Define SQLAlchemy models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    recipes = relationship('Recipe', backref='user', lazy=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    preparation_steps = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer, nullable=False)
    serving_size = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Float)

with app.app_context():
    db.create_all()

# Define Marshmallow schemas
class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
    id = ma.auto_field()
    username = ma.auto_field()
    email = ma.auto_field()

class RecipeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Recipe
    id = ma.auto_field()
    title = ma.auto_field()
    description = ma.auto_field()
    ingredients = ma.auto_field()
    preparation_steps = ma.auto_field()
    cooking_time = ma.auto_field()
    serving_size = ma.auto_field()
    category = ma.auto_field()
    user_id = ma.auto_field()
    rating = ma.auto_field()

# Authentication endpoints
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    new_user = User(username=data['username'], email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message='User created successfully'), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify(message='Invalid credentials'), 401

# CRUD endpoints for recipes
@app.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    current_user_id = get_jwt_identity()
    data = request.json
    new_recipe = Recipe(
        title=data['title'],
        description=data['description'],
        ingredients=data['ingredients'],
        preparation_steps=data['preparation_steps'],
        cooking_time=data['cooking_time'],
        serving_size=data['serving_size'],
        category=data['category'],
        user_id=current_user_id
    )
    db.session.add(new_recipe)
    db.session.commit()
    return jsonify(message='Recipe created successfully'), 201

# CRUD endpoints for recipes
@app.route('/recipes', methods=['GET'])
@jwt_required()
def get_all_recipes():
    current_user_id = get_jwt_identity()
    recipes = Recipe.query.filter_by(user_id=current_user_id).all()
    recipe_schema = RecipeSchema(many=True)
    return recipe_schema.jsonify(recipes), 200


@app.route('/recipes/<int:id>', methods=['GET'])
@jwt_required()
def get_recipe(id):
    current_user_id = get_jwt_identity()

    recipe = Recipe.query.filter_by(id=id, user_id=current_user_id).first()
    if not recipe:
        return jsonify(message='Recipe not found'), 404
    recipe_schema = RecipeSchema()
    return recipe_schema.jsonify(recipe), 200

@app.route('/recipes/<int:id>', methods=['PUT'])
@jwt_required()
def update_recipe(id):
    current_user_id = get_jwt_identity()

    recipe = Recipe.query.filter_by(id=id, user_id=current_user_id).first()
    if not recipe:
        return jsonify(message='Recipe not found'), 404
    data = request.json
    recipe.title = data['title']
    recipe.description = data['description']
    recipe.ingredients = data['ingredients']
    recipe.preparation_steps = data['preparation_steps']
    recipe.cooking_time = data['cooking_time']
    recipe.serving_size = data['serving_size']
    recipe.category = data['category']
    db.session.commit()
    return jsonify(message='Recipe updated successfully'), 200

@app.route('/recipes/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_recipe(id):
    current_user_id = get_jwt_identity()

    recipe = Recipe.query.filter_by(id=id, user_id=current_user_id).first()
    if not recipe:
        return jsonify(message='Recipe not found'), 404
    db.session.delete(recipe)
    db.session.commit()
    return jsonify(message='Recipe deleted successfully'), 200


@app.route('/recipes/category/<string:category>', methods=['GET'])
@jwt_required()
def get_recipes_by_category(category):
    current_user_id = get_jwt_identity()
    recipes = Recipe.query.filter_by(category=category, user_id=current_user_id).all()
    if not recipes:
        return jsonify(message=f'No recipes found in category: {category}'), 404
    recipe_schema = RecipeSchema(many=True)
    return recipe_schema.jsonify(recipes), 200


if __name__ == '__main__':
    app.run(debug=True)
