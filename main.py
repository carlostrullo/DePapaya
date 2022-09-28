import requests
import random
import time
import logging
import firebase_admin
from firebase_admin import credentials,auth
from flask import Flask, json,request
import google.auth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os
import sendgrid
from sendgrid.helpers import mail


app=Flask(__name__)

credentials, project = google.auth.default()
default_app = firebase_admin.initialize_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#db_user = os.environ.get('CLOUD_SQL_USERNAME')
#db_password = os.environ.get('CLOUD_SQL_PASSWORD')
#db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
#db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
#unix_socket = '/cloudsql/{}'.format(db_connection_name)
#db = pymysql.connect(user=db_user, password=db_password,unix_socket=unix_socket, db=db_name)


SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
SENDGRID_SENDER = os.environ['SENDGRID_SENDER']



@app.route("/verificarToken", methods=['POST'])
def verificarToken():
  valor = request.get_json()
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  uid = decoded_token['uid']
  response= {'token':uid}
  return json.dumps(response)




@app.route("/listarRestaurantes", methods=['POST'])
def listarTodos():
  valor = request.get_json()
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM Restaurante"))
  return json.dumps([dict(r) for r in mycursor])


@app.route("/busquedaPalabras", methods=['POST'])
def busquedaPalabras():
  valor = request.get_json()
  rest=valor['rest']
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM depapaya.Restaurante WHERE MATCH (Nombre, Descripcion, Categoria, Zona, Tipo) AGAINST("+rest+")"))
  return json.dumps([dict(r) for r in mycursor])


@app.route("/listarRecomendados", methods=['POST'])
def listarRecomendado():
  valor = request.get_json()
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM Recomendado"))
  return json.dumps([dict(r) for r in mycursor])



@app.route("/listarPromos", methods=['POST'])
def listarPromociones():
  valor = request.get_json()
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM Promocion"))
  return json.dumps([dict(r) for r in mycursor])



@app.route("/cerca", methods=['POST'])
def restaurantesCerca():
  valor = request.get_json()
  lat=valor['latitude']
  long=valor['longitude']
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT *, (6371 * ACOS(SIN(RADIANS(Latitude)) * SIN(RADIANS("+lat+")) + COS(RADIANS(Longitude - "+long+")) * COS(RADIANS(Latitude))"+ 
   "* COS(RADIANS("+lat+")))) as distancia FROM Restaurante HAVING distancia <= 4 ORDER BY distancia ASC"))
  return json.dumps([dict(r) for r in mycursor])


@app.route("/fotosRestaurante", methods=['POST'])
def fotosRestaurante():
  valor = request.get_json()
  rest=valor['rest']
  mycursor=db.engine.execute(text("SELECT Foto FROM GaleriaRestaurante where NombreRestaurante="+rest))
  return json.dumps([dict(r) for r in mycursor])


@app.route("/comidaRestaurante", methods=['POST'])
def comidaRestaurante():
  valor = request.get_json()
  rest=valor['rest']
  mycursor=db.engine.execute(text("SELECT Foto FROM Menu where MenuRest="+rest))
  return json.dumps([dict(r) for r in mycursor])



@app.route("/listarCategoria", methods=['POST'])
def listarCategoria():
  valor = request.get_json()
  rest=valor['rest']
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM Restaurante where Categoria ="+rest))
  return json.dumps([dict(r) for r in mycursor])



@app.route("/listarPrecios", methods=['POST'])
def listarPrecios():
  valor = request.get_json()
  rest=valor['rest']
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM Restaurante where Precio <="+rest+" ORDER BY Precio"))
  return json.dumps([dict(r) for r in mycursor])



@app.route("/restauranteNombre", methods=['POST'])
def restauranteNombre():
  valor = request.get_json()
  rest=valor['rest']
  mycursor=db.engine.execute(text("SELECT * FROM Restaurante where Nombre ="+rest))
  return json.dumps([dict(r) for r in mycursor])


@app.route("/busquedaZona", methods=['POST'])
def busquedaZona():
  valor = request.get_json()
  rest=valor['rest']
  tok=valor['token']
  decoded_token = auth.verify_id_token(tok)
  mycursor=db.engine.execute(text("SELECT * FROM Restaurante where Zona ="+rest))
  return json.dumps([dict(r) for r in mycursor])


@app.route("/realizarReserva", methods=['POST'])
def realizarReserva():
 valor = request.get_json()
 nombre=valor['nombre']
 personas=valor['personas']
 fecha=valor['fecha']
 hora=valor['hora']
 motivo=valor['motivo']
 contacto=valor['contacto']
 restaurante=valor['restaurante']
 tok=valor['token']
 decoded_token = auth.verify_id_token(tok)

 sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
 to_email = mail.Email('depapaya.web@gmail.com')
 from_email = mail.Email(SENDGRID_SENDER)
 subject = 'Reserva'
 content = mail.Content("text/plain", 'Restaurante :'+restaurante +' Nombre:'+nombre +' Personas:'+personas+ ' Fecha:'+fecha +' Hora:'+hora+motivo+' Contacto:'+contacto)
 message = mail.Mail(from_email, subject, to_email, content)
 response = sg.client.mail.send.post(request_body=message.get())
 if response.status_code != 202:
     return 'An error occurred: {}'.format(response.body), 500

 return 'Email sent.'


if __name__ == "__main__":
  app.run(host='127.0.0.1', port=8080, debug=True)
