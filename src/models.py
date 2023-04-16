from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    subscription_date = db.Column(db.String, nullable=False)
    birth_date = db.Column(db.Integer)
    country = db.Column(db.String)
    favorite_people = db.relationship("FavoritePeople", backref="user", lazy=True)
    favorite_planet = db.relationship("FavoritePlanets", backref="user", lazy=True)
    favorite_vehicle = db.relationship("FavoriteVehicles", backref="user", lazy=True)

    def __repr__(self):
        return '<User %r>' % self.first_name

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name":self.first_name,
            "last_name":self.last_name,
            "subscription_date":self.subscription_date,
            "birth_date":self.birth_date,
            "country":self.country,

            # do not serialize the password, its a security breach
        }

class People(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, nullable=False)
    url = db.Column(db.String(50), nullable=False)
    height = db.Column(db.Float(), nullable=False)
    mass = db.Column(db.Float(), nullable=False)
    hair_color=db.Column(db.String(50), nullable=False)
    skin_color=db.Column(db.String(50), nullable=False)
    eyes_color=db.Column(db.String(50), nullable=False)
    birth_year = db.Column(db.Float(), nullable=False)
    gender=db.Column(db.String(50), nullable=False)
    favorite_people = db.relationship("FavoritePeople", backref="people", lazy=True) # la propiedad backref, lo que hace es entregarle todas las propiedades de People a FavoritePeople

    def serialize(self):
        return {
            "uid": self.uid,
            "name":self.name,
            "url":self.url,
            "height":self.height,
            "mass": self.mass,
            "hair_color":self.hair_color,
            "skin_color":self.skin_color,
            "skin_color":self.eyes_color,
            "birth_year":self.birth_year,
            "gender":self.gender,
            # do not serialize the password, its a security breach
        }

class Planets(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, nullable=False)
    url = db.Column(db.String(50), nullable=False)
    diameter = db.Column(db.Float(), nullable=False)
    rotation_period = db.Column(db.Float(), nullable=False)
    orbital_period = db.Column(db.Integer, nullable=False)
    gravity = db.Column(db.Float(), nullable=False)
    population = db.Column(db.Float(), nullable=False)
    climate = db.Column(db.String, nullable=False)
    favorite_planet = db.relationship("FavoritePlanets", backref="planets", lazy=True)
    
    def serialize(self):
        return {
            "uid": self.uid,
            "name":self.name,
            "url":self.url,
            "diameter":self.diameter,
            "rotation_period": self.rotation_period,
            "orbital_period":self.orbital_period,
            "gravity":self.gravity,
            "Population":self.population,
            "climate":self.climate,
 
            # do not serialize the password, its a security breach
        }


class Vehicles(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, nullable=False)
    url = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String, nullable=False)
    vehicle_class = db.Column(db.String, nullable=False)
    manufacturer = db.Column(db.String, nullable=False)
    cost_in_credits = db.Column(db.Float(), nullable=False)
    passengers = db.Column(db.Integer, nullable=False)
    cargo_capacity = db.Column(db.Float(), nullable=False)
    favorite_vehicle = db.relationship("FavoriteVehicles", backref="vehicles", lazy=True)

    def serialize(self):
        return {
            "uid": self.uid,
            "name":self.name,
            "url":self.url,
            "model":self.model,
            "vehicle_class": self.vehicle_class,
            "manufacturer":self.manufacturer,
            "cost_in_credits":self.cost_in_credits,
            "passengers":self.passengers,
            "cargo_capacity":self.cargo_capacity,
 
            # do not serialize the password, its a security breach
        }


class FavoritePeople(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    people_uid = db.Column(db.Integer, db.ForeignKey("people.uid"), nullable=False) 
    
    def serialize(self):
        return {
            "id": self.id,
            "user_id":self.user_id,  
            "people_uid":self.people_uid,
            "people_name": People.query.get(self.people_uid).serialize()["name"],
            "user_first_name": User.query.get(self.user_id).serialize()["first_name"],
            "people":People.query.get(self.people_uid).serialize(),
            "user": User.query.get(self.user_id).serialize(),

            
            # do not serialize the password, its a security breach
        }

class FavoritePlanets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    planet_uid = db.Column(db.Integer, db.ForeignKey("planets.uid"), nullable=False) 
    
    def serialize(self):
        return {
            "id": self.id,
            "user_id":self.user_id,
            "planet_uid":self.planet_uid,
            #PARA OBTENER UNA PROPIEDAD ENE ESPECIFICO 
            # "planet_name": Planets.query.get(self.planet_uid).serialize()["name"],
            # "user_first_name": User.query.get(self.user_id).serialize()["first_name"],
            #PARA OBTENER TODAS LAS PROPIEDADES DE UNA TABLA
            "planets":Planets.query.get(self.planet_uid).serialize(),
            "user": User.query.get(self.user_id).serialize(),
            # do not serialize the password, its a security breach
        }

class FavoriteVehicles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    vehicle_uid = db.Column(db.Integer, db.ForeignKey("vehicles.uid"), nullable=False) 
    
    def serialize(self):
        return {
            "id": self.id,
            "user_id":self.user_id,
            "vehicle_uid":self.vehicle_uid, 
            "vehicles":Vehicles.query.get(self.vehicle_uid).serialize(),
            "user": User.query.get(self.user_id).serialize(), 
            
            # do not serialize the password, its a security breach
        }

#MODELO DE BASE DE DATOS PARA BLOQUEAR EL TOQUEN UNA VEZ EL USUARIO HACE LOGOUT.

class TokenBlokedList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False) #Se recomienda el uso del ID en lugar del email, se hace aquí como práctica. Igual, podría ser un ForengnKey
    create_at =db.Column(db.DateTime, nullable=False)
    is_blocked = db.Column(db.Boolean, default=True)

    def serialize(self):
        return{
            "id":self.id,
            "token":self.token,
            "email":self.email,
            "create_at":self.create_at,
            "is_bloqued":self.is_blocked,
        }