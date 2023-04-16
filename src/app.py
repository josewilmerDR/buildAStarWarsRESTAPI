"""This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, Vehicles, FavoritePeople, FavoritePlanets, FavoriteVehicles, TokenBlokedList
import json

#PARA MANEJAR LA ENCRIPTACIÓN DE LA INFORMACIÓN. ADICIONAL SE REQUIERE, FLASK, REQUEST, JSONIFY, SIN EMBARGO ESOS YA FUERON INSTALADOS ARRIBA.
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

#PARA OPERACIONES CON FECHAS Y HORAS.
from datetime import date, time, datetime, timezone, timedelta #timedelta, es para hacer resta de horas.

#PARA ENCRIPTAR EL PASSWORD
from flask_bcrypt import Bcrypt

#INSTANCIA DE FLASK
app = Flask(__name__)
app.url_map.strict_slashes = False

# Setup the Flask-JWT-Extended extension - relacionado con la encripción.
app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_APP_KEY") # recuerda que debes tener la variable de ambiente "FLASK_APP_KEY" en tu archivo .env
jwt = JWTManager(app)  

#ENCRIPTAMOS LA INSTANCIA APP
bcrypt = Bcrypt(app)
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

#Verificación de token:
def verificacionToken(identity):
    jti = identity["jti"]
    token = TokenBlokedList.query.filter_by(token=jti, is_blocked=True).first()
    
    if token:
        return True  # Token bloqueado
    else:
        return False  # Token no bloqueado
    

#1 - [GET] /people Listar todos los registros de people en la base de datos

@app.route('/people', methods=['GET'])
def get_people():

    people = People.query.all()
    people = list(map(lambda item: item.serialize(), people))
    print(people)

    return jsonify(people), 200

#2 - [GET] /people/<int:people_id> Listar la información de una sola people
@app.route('/people/<int:uid>', methods=['GET'])
def get_specific_character(uid):

    character = People.query.get(uid)

    return jsonify(character.serialize()), 200

#3 - [GET] /planets Listar los registros de planets en la base de datos
@app.route('/planets', methods=['GET'])
def get_planets():

    planets = Planets.query.all()
    planets = list(map(lambda item: item.serialize(), planets))
    print(planets)

    return jsonify(planets), 200

#4 - [GET] /planets/<int:planet_id> Listar la información de un solo planet
@app.route('/planets/<int:uid>', methods=['GET'])
def get_specific_planet(uid):

    planet = Planets.query.get(uid)

    return jsonify(planet.serialize()), 200

#5 - [GET] /users Listar todos los usuarios del blog
@app.route('/user', methods=['GET'])
def handle_hello():

    users = User.query.all()
    users = list(map(lambda item: item.serialize(), users))
    print(users)

    return jsonify(users), 200

#6 - [GET] /users/favorites Listar todos los favoritos que pertenecen al usuario actual.

#OBTENER TODOS LOS FAVORITOS
@app.route('/favorites', methods=['POST'])
def list_favorites():
    body = request.get_json()
    user_id = body["user_id"]
    
    if not user_id:
        raise APIException({"message":"Necesario user_id"}, status_code=404)

    user = User.query.get(user_id)
    
    if not user:
        raise APIException("Usuario no encontrado", 404)

    # AGREGAR LOS PERSONAJES FAVORITOS
    user_favorites_people = FavoritePeople.query.filter_by(user_id=user.id).all()
    user_favorites_people = list(map(lambda item:item.serialize(), user_favorites_people))

    # AGREGAR LOS VEHICULOS FAVORITOS

    user_favorites_vehicles = FavoriteVehicles.query.filter_by(user_id=user.id).all()
    user_favorites_vehicles = list(map(lambda item:item.serialize(), user_favorites_vehicles))


    # AGREGAR LOS PLANETAS FAVORITOS

    user_favorites_planets = FavoritePlanets.query.filter_by(user_id=user.id).all()
    user_favorites_planets = list(map(lambda item:item.serialize(), user_favorites_planets))

    #UNA OPCION PARA SUMAR FAVORITOS CON .APPEND()
    # user_favorites = user_favorites_people.append(user_favorites_vehicles)
    # user_favorites = user_favorites.append(user_favorites_planets)
    
    #OPCION RECOMENDADA PARA SUMAR LOS FAVORITOS  
    user_favorites = user_favorites_people + user_favorites_vehicles + user_favorites_planets
    
    
    return jsonify(user_favorites), 200 

#7 - [POST] /favorite/planet/<int:planet_id> Añade un nuevo planet favorito al usuario actual con el planet id = planet_id
# @app.route('/aplanets/<int:planet_id>', methods=['POST'])
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    body = request.get_json()
    user_id = body["user_id"]

    planet = Planets.query.get(planet_id) #Se filtra el planeta actual.

    if not planet:
        raise APIException("Planeta no encontrado", 404)

    user = User.query.get(user_id) # se filtra el usuario al que se le desea agregar el planeta.

    if not user:
        raise APIException("Usuario no encontrado", 404)

    #Básicamente, estamos buscando si hay una coincidencia en la tabla FavoritePlanets que tenga el mismo user_id y planet_uid.
    fav_exist = FavoritePlanets.query.filter_by(user_id=user.id, planet_uid=planet.uid).first() is not None

    if fav_exist:
        raise APIException("El usuario ya ha agregado este planeta como favorito", 404)

    favorite_planet = FavoritePlanets(user_id=user.id, planet_uid=planet.uid)
    db.session.add(favorite_planet)
    db.session.commit()

    return jsonify(favorite_planet.serialize()), 200

#8 - [POST] /favorite/people/<int:people_id> Añade una nueva people favorita al usuario actual con el people.id = people_id.
@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    body = request.get_json()
    user_id = body["user_id"]

    character = People.query.get(people_id)

    if not character:
        raise APIException("Planeta no encontrado", 404)

    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", 404)

    fav_exist = FavoritePeople.query.filter_by(user_id=user.id, people_uid=character.uid).first() is not None

    if fav_exist:
        raise APIException("El usuario ya ha agregado este planeta como favorito", 404)

    favorite_people = FavoritePeople(user_id=user.id, people_uid=character.uid)
    db.session.add(favorite_people)
    db.session.commit()

    return jsonify(favorite_people.serialize()), 200

#9 - [DELETE] /favorite/planet/<int:planet_id> Elimina un planet favorito con el id = planet_id

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    body = request.get_json()
    user_id = body["user_id"]

    planet = Planets.query.get(planet_id)

    if not planet:
        raise APIException("Planeta no encontrado", 404)

    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", 404)

    favorite_planet = FavoritePlanets.query.filter_by(user_id=user.id, planet_uid=planet.uid).first()

    if not favorite_planet:
        raise APIException("Planeta no encontrado en los favoritos del usuario", 404)

    db.session.delete(favorite_planet)
    db.session.commit()

    return jsonify({"message": "Planeta eliminado de favoritos correctamente"}), 200

#10 - [DELETE] /favorite/people/<int:people_id> Elimina una people favorita con el id = people_id.

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    body = request.get_json()
    user_id = body["user_id"]

    character = People.query.get(people_id)

    if not character:
        raise APIException("Personaje no encontrado", 404)

    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", 404)

    favorite_people = FavoritePeople.query.filter_by(user_id=user.id, people_uid=character.uid).first()

    if not favorite_people:
        raise APIException("Personaje no encontrado en los favoritos del usuario", 404)

    db.session.delete(favorite_people)
    db.session.commit()

    return jsonify({"message": "Planeta eliminado de favoritos correctamente"}), 200

# 11 - +4 Crea API Endpoints para agregar (POST), modificar (PUT) y eliminar (DELETE) planets y people. 
# De esta manera, toda la base de datos va a poder ser administrada via API.

# 11.a - AGREGAR PLANETA:
#Solo usurios registrados pueden crear nuevos planetas.

@app.route('/add/planet', methods=['POST'])
@jwt_required()
def add_planet():
    body = request.get_json() #tambien con .json()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos planetas"})

    name = body["name"]
    url = body["url"]
    diameter = body["diameter"]
    rotation_period = body["rotation_period"]
    orbital_period = body["orbital_period"]
    gravity = body["gravity"]
    population = body["population"]
    climate = body["climate"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "climate" not in body:
        raise APIException({"message":"necesitas especificar el uid"}, status_code=400)
    if "url" not in body:
        raise APIException({"message":"necesitas especificar la url"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)
  
    new_planet = Planets(name=name, url=url, diameter=diameter, rotation_period=rotation_period, orbital_period=orbital_period, gravity=gravity, population=population, climate=climate)
    db.session.add(new_planet)
    db.session.commit()
 
    return jsonify({"message":"Planeta creado correctamente user"}), 201

# 11.b - AGREGAR PEOPLE:
#Solo usurios registrados pueden crear nuevos personajes.

@app.route('/add/people', methods=['POST'])
@jwt_required()
def add_people():
    body = request.get_json() #tambien con .json()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos planetas"})

    name = body["name"]
    url = body["url"]
    height = body["height"]
    mass = body["mass"] 
    hair_color = body["hair_color"]
    skin_color = body["skin_color"] 
    eyes_color = body["eyes_color"] 
    birth_year = body["birth_year"]
    gender = body["gender"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "gender" not in body:
        raise APIException({"message":"necesitas especificar el genero"}, status_code=400)
    if "url" not in body:
        raise APIException({"message":"necesitas especificar la url"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)
  
    new_people = Planets(name=name, url=url, height=height, mass=mass, hair_color=hair_color, skin_color=skin_color, eyes_color=eyes_color, birth_year=birth_year, gender=gender)
    db.session.add(new_planet)
    db.session.commit()
 
    return jsonify({"message":"Planeta creado correctamente user"}), 201

# 11.c - AGREGAR VEHICULO:
#Solo usurios registrados pueden crear nuevos vehículos.


@app.route('/add/vehiculo', methods=['POST'])
@jwt_required()
def add_vehiculo():
    body = request.get_json() #tambien con .json()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos vehículos"})

    name = body["name"]
    url = body["url"]
    model = body["model"]
    vehicle_class = body["vehicle_class"]
    manufacturer = body["manufacturer"]
    cost_in_credits = body["cost_in_credits"]
    passengers = body["passengers"]
    cargo_capacity = body["cargo_capacity"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "model" not in body:
        raise APIException({"message":"necesitas especificar el modelo"}, status_code=400)
    if "url" not in body:
        raise APIException({"message":"necesitas especificar la url"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)
  
    new_people = Planets(name=name, url=url, model=model, vehicle_class=vehicle_class, manufacturer=manufacturer, cost_in_credits=cost_in_credits, passengers=passengers, cargo_capacity=cargo_capacity)
    db.session.add(new_planet)
    db.session.commit()
 
    return jsonify({"message":"Planeta creado correctamente user"}), 201

#11-d - EDITAR PLANET
@app.route('/update/planet', methods=['PUT'])
@jwt_required()
def update_planet():
    body = request.get_json() #tambien con .json()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos planetas"})
    uid = body["uid"]
    name = body["name"]
    url = body["url"]
    diameter = body["diameter"]
    rotation_period = body["rotation_period"]
    orbital_period = body["orbital_period"]
    gravity = body["gravity"]
    population = body["population"]
    climate = body["climate"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "climate" not in body:
        raise APIException({"message":"necesitas especificar el uid"}, status_code=400)
    if "url" not in body:
        raise APIException({"message":"necesitas especificar la url"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)
  

    planet = Planets.query.get(uid)

    planet.name = name
    planet.url = url
    planet.diameter = diameter
    planet.rotation_period = rotation_period
    planet.orbital_period = orbital_period
    planet.gravity = gravity
    planet.population = population
    planet.climate = climate

    db.session.commit()
  
    return jsonify({"message":"Planeta editado correctamente user"}), 201


#11.e - actualizar un personaje
@app.route('/update/people', methods=['PUT'])
@jwt_required()
def update_people():
    
    body = request.get_json() #tambien con .json()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos planetas"})

    uid = body["uid"]
    name = body["name"]
    url = body["url"]
    height = body["height"]
    mass = body["mass"] 
    hair_color = body["hair_color"]
    skin_color = body["skin_color"] 
    eyes_color = body["eyes_color"] 
    birth_year = body["birth_year"]
    gender = body["gender"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "gender" not in body:
        raise APIException({"message":"necesitas especificar el genero"}, status_code=400)
    if "url" not in body:
        raise APIException({"message":"necesitas especificar la url"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400) 

    people = People.query.get(uid)
    people.uid = uid
    people.name = name
    people.url = url
    people.height = height
    people.mass = mass
    people.hair_color = hair_color
    people.eyes_color = eyes_color
    people.birth_year = birth_year
    people.gender = gender
 
    db.session.commit()

    return jsonify({"message":"Personaje editado correctamente user"}), 201

# 11.f - AGREGAR VEHICULO:
#Solo usurios registrados pueden crear nuevos vehículos.


@app.route('/update/vehiculo', methods=['POST'])
@jwt_required()
def update_vehiculo():
    body = request.get_json() #tambien con .json()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos vehículos"})

    name = body["name"]
    url = body["url"]
    model = body["model"]
    vehicle_class = body["vehicle_class"]
    manufacturer = body["manufacturer"]
    cost_in_credits = body["cost_in_credits"]
    passengers = body["passengers"]
    cargo_capacity = body["cargo_capacity"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "model" not in body:
        raise APIException({"message":"necesitas especificar el modelo"}, status_code=400)
    if "url" not in body:
        raise APIException({"message":"necesitas especificar la url"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)


    vehicle = Vehicles.query.get(uid)
    vehicle.uid = uid
    vehicle.name = name
    vehicle.url = url
    vehicle.model = model
    vehicle.vehicle_class = vehicle_class
    vehicle.manufacturer = manufacturer
    vehicle.cost_in_credits = cost_in_credits
    vehicle.passengers = passengers
    vehicle.cargo_capacity = cargo_capacity
    db.session.commit()

    return jsonify({"message":"Vehículo editado correctamente user"}), 201

#11-g - ELIMINAR UN PLANETA
@app.route('/delete/planet', methods=['DELETE'])
@jwt_required()
def delete_specific_planet():

    body = request.get_json()

    token = verificacionToken(get_jwt())
    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos vehículos"})
    
    uid=body["uid"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "uid" not in body:
        raise APIException({"message":"necesitas especificar el uid del planeta a eliminar"}, status_code=400)
    

    planet = Planets.query.get(uid)

    db.session.delete(planet)
    db.session.commit()

    return jsonify({"message":"Planeta eliminado exitosamente"}), 200


#11-h - ELIMINAR UN PERSONAJE
@app.route('/delete/people', methods=['DELETE'])
@jwt_required()
def delete_specific_people():

    body = request.get_json()

    token = verificacionToken(get_jwt())
    if token:
        raise APIException({"message":"Inicia sesión para crear nuevos vehículos"})
    
    uid=body["uid"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "uid" not in body:
        raise APIException({"message":"necesitas especificar el uid del personaje a eliminar"}, status_code=400)
    

    people = People.query.get(uid)

    db.session.delete(people)
    db.session.commit()

    return jsonify({"message":"Personaje eliminado exitosamente"}), 200


#11-i - ELIMINAR UN VEHICULO
@app.route('/delete/vehicle', methods=['DELETE'])
@jwt_required()
def delete_specific_vehicle():

    body = request.get_json()

    token = verificacionToken(get_jwt())
    if token:
        raise APIException({"message":"Inicia sesión para eliminar vehículos"})
    
    uid=body["uid"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "uid" not in body:
        raise APIException({"message":"necesitas especificar el uid del vehículo a eliminar"}, status_code=400)
    

    vehicles = Vehicles.query.get(uid)

    db.session.delete(vehicles)
    db.session.commit()

    return jsonify({"message":"Vehículo eliminado exitosamente"}), 200

#OTRAS SOLICITUDES

#1 - Registrar un usuario
@app.route('/register', methods=['POST'])
def register_user():
    body = request.get_json() #tambien con .json()
  
    email = body["email"]
    first_name = body["first_name"]
    last_name = body["last_name"]
    password = body["password"]
    is_active = body["is_active"]
    subscription_date = body["subscription_date"]
    birth_date = body["birth_date"]
    country = body["country"]

    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "email" not in body:
        raise APIException({"message":"necesitas especificar el email"}, status_code=400)
    if "first_name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)
    if "password" not in body:
        raise APIException({"message":"necesitas especificar el password"}, status_code=400)
  
    #ENCRIPTAMOS LA CONTRASEÑA DEL USUARIO ANTES DE ALMACENARLA EN BASE DE DATOS.
    password_escrypted = bcrypt.generate_password_hash(password, 10).decode('utf-8')

    new_user = User(email=email, first_name=first_name, last_name=last_name, password=password_escrypted, is_active=is_active, subscription_date=subscription_date,birth_date=birth_date, country=country)
    db.session.add(new_user)
    db.session.commit()
 
    return jsonify({"message":"Correct created user"}), 201

#2 - Obtener un usuario específico usando GET
@app.route('/user/<int:id>', methods=['GET'])
def get_specific_user_using_GET(id):

    user = User.query.get(id)

    return jsonify(user.serialize()), 200


#3 - Obtener un usuario específico usando POST
@app.route('/user', methods=['POST'])
def get_specific_user_using_POST():

    body = request.get_json()

    id=body["id"]

    user = User.query.get(id)

    return jsonify(user.serialize()), 200


#4 - Elimina un usuario
@app.route('/user/delete', methods=['DELETE'])
def delete_specific_user():

    body = request.get_json()

    id=body["id"]

    user = User.query.get(id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message":"usuario borrado"}), 200


#5 - actualizar un usuario
@app.route('/user/update', methods=['PUT'])
def edit_user():
    body = request.get_json()
    
    id=body["id"]
    email = body["email"]
    first_name = body["first_name"]
    last_name = body["last_name"]
    password = body["password"]
    is_active = body["is_active"]
    subscription_date = body["subscription_date"]
    birth_date = body["dirth_date"]
    country = body["country"]

    #VALIDACIONES
    if body is None:
        raise APIException({"message":"necesitas especificar el body"}, status_code=400)
    if "email" not in body:
        raise APIException({"message":"necesitas especificar el email"}, status_code=400)
    if "name" not in body:
        raise APIException({"message":"necesitas especificar el name"}, status_code=400)
    if "password" not in body:
        raise APIException({"message":"necesitas especificar el password"}, status_code=400)

    user = User.query.get(id)
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.password = password
    user.is_active = is_active
    user.subscription_date = subscription_date
    user.birth_date = birth_date
    user.country = country

    db.session.commit()
    # user = User(email=email, name=name, password=password, is_active=is_active)
    # db.session.commit()

    return jsonify(user.serialize()), 200


#6 - agregar favoritos usando POST.
@app.route('/add-favorite/people', methods=['POST'])
def add_favorite_people_any_user():
    body = request.get_json()
    user_id = body["user_id"]
    people_uid = body["people_uid"]

    character = People.query.get(people_uid)

    if not character:
        raise APIException("Personaje no encontrado", 404)
    
    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", 404)


    #SI NO EXISTE EL FAVORITO aregarlo, SI NO 

    fav_exist = FavoritePeople.query.filter_by(user_id=user.id, people_uid=character.uid).first() is not None

    if fav_exist:
        raise APIException("El usuario ya lo tienes agregado a favoritos", 404)

    favorite_people = FavoritePeople(user_id = user.id, people_uid = character.uid)
    db.session.add(favorite_people)
    db.session.commit()

    return jsonify(favorite_people.serialize()), 200


#7 - [POST] /favorite/vehicle/<int:vehicle_id> Añade un nuevo vehículo al usuario actual con el vehicle.id = vehicle_id.
@app.route('/favorite/vehicle/<int:vehicle_id>', methods=['POST'])
def add_favorite_vehicle(vehicle_id):
    body = request.get_json()
    user_id = body["user_id"]

    vehicle = Vehicles.query.get(vehicle_id)

    if not vehicle:
        raise APIException("Vehículo no encontrado", 404)

    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", 404)

    fav_exist = FavoriteVehicles.query.filter_by(user_id=user.id, vehicle_id=vehicle.uid).first() is not None

    if fav_exist:
        raise APIException("El usuario ya ha agregado este vehículo como favorito", 404)

    favorite_vehicle = FavoriteVehicles(user_id=user.id, vehicle_id=vehicle.uid)
    db.session.add(favorite_vehicle)
    db.session.commit()

    return jsonify(favorite_vehicle.serialize()), 200


#8 - [DELETE] /favorite/vehicle/<int:vehicle_id> Elimina un vehículo favorito con el id = planet_id
@app.route('/favorite/vehicle/<int:vehicle_id>', methods=['DELETE'])
def delete_favorite_vehicle(vehicle_id):
    body = request.get_json()
    user_id = body["user_id"]

    vehicle = Vehicles.query.get(vehicle_id)

    if not vehicle:
        raise APIException("Vehículo no encontrado", 404)

    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", 404)

    favorite_vehicle = FavoriteVehicles.query.filter_by(user_id=user.id, vehicle_id=vehicle.uid).first()

    if not favorite_vehicle:
        raise APIException("Vehículo no encontrado en los favoritos del usuario", 404)

    db.session.delete(favorite_vehicle)
    db.session.commit()

    return jsonify({"message": "Planeta eliminado de favoritos correctamente"}), 200


#9 - ENDPOINT LOGIN.
@app.route('/login', methods=["POST"])  # Corrected the methods parameter
def login():
    email = request.get_json()["email"]
    password = request.get_json()["password"]

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"message": "usuario o contraseña incorrecta"})

    #VALIDACION DE LA CONTRASEÑA EN TEXTO PLANO, NO FUNCIONA PARA CONEXIONES ENCRIPTADAS, DADO QUE LA VALIDACIÓN SE HACE ANTES DE ENCRITPTAR EL PASSWORD. USA bcrypt.check_password_hash(pw_hash, candidate), PARA VALIDAR EL PASSWORD ENCRYTADO.
    # if password != user.password:
    #     return jsonify({"message": "usuario o contraseña incorrecta"})

    if not bcrypt.check_password_hash(user.password, password): #se compara la contrese encriptada, contra la contraseña encrytada que llega desde el usuario.
        return jsonify({"message": "usuario o contraseña incorrecta"})

    # Validación del email.    
    if email != user.email:
        return jsonify({"message": "usuario o contraseña incorrecta"})

    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token}), 200

#10 - ENDPOINT PROTEGIDO
# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    user = User.query.get(current_user)

    # #validar si el token existe como bloqueado.
    # jti = get_jwt()["jti"]
    # token = TokenBlokedList.query.filter_by(token=jti, is_blocked=True).first()

    #VALIDAR si el token existe como bloqueado, con una función previamente definiada.
    token = verificacionToken(get_jwt())

    if token:
        raise APIException({"message":"Inicia sesión para ir a esta rura protegida"})    

    print("El usuario actual es: ", user.first_name)
    print("El usuario actual es: ", current_user)
    return jsonify({"message":"Estas en una ruta protegida"}), 200

#11 - LOGOUT DEL USUARIO.
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # Access the identity of the current user with get_jwt_identity
    jti = get_jwt()["jti"] #PARA OBTENER Y ALMACENAR EL IDENTIFICADOR DEL TOKEN DEL USUARIO AL MOMENTO QUE HACE LOGOUT, ESTO REDUCE EL ESPACIO REQUERIDO PARA ALMACENAMIENTO DE LOS MISMOS
    now = datetime.now(timezone.utc)
    
    #identificando al usuario:
    current_user = get_jwt_identity()
    user = User.query.get(current_user)

    token_bloked = TokenBlokedList(token=jti, create_at=now, email=user.email)
    
    #FORMA ALTERNA DE ASGINAR VALORES A PROPIEDADES DE LA CLASE TokenBlokedList
    # token_bloked = TokenBlokedList()
    # token_bloked.token = jti
    # token_bloked.create_at = now
    # token_bloked.email=user.email

    #Guardamos la información en base de datos.
    db.session.add(token_bloked)
    db.session.commit()
    return jsonify({"message":"logout successfully"}), 200


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
