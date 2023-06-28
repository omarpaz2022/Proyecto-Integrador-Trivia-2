import flask
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy
#from flask_bootstrap import Bootstrap
from sqlalchemy import func
from flask import session
import os

Base = declarative_base()
db = SQLAlchemy()

class Preguntas(Base):
    __tablename__ = 'preguntas'
    pregunta = Column(Text, primary_key=True)
    res1 = Column(Text)
    res2 = Column(Text)
    res3 = Column(Text)
    res4 = Column(Text)
    correcta = Column(Text)
    jugadas = db.relationship("Jugada", backref="pregunta", lazy=True)

class Jugador(Base):
    __tablename__ = 'jugador'
    id = Column(Integer, primary_key=True)
    nombre = Column(Text)
    puntaje = Column(Integer)
    jugadas = db.relationship("Jugada", backref="jugador", lazy=True)

class Jugada(Base):
    __tablename__ = 'jugada'
    jugador_id = Column(Integer, db.ForeignKey("jugador.id"), primary_key=True)
    pregunta_id = Column(Text, db.ForeignKey("preguntas.pregunta"), primary_key=True)
    puntaje = Column(Integer)
    respuesta = Column(Text())

    @property
    def pk(self):
        return self.jugador_id, self.pregunta_id

    @pk.setter
    def pk(self, value):
        self.jugador_id, self.pregunta_id = value

base_dir = os.path.abspath(os.path.dirname(__file__))
db_file = "juegodb.db"
db_path = os.path.join(base_dir, db_file)

app = Flask(__name__)
app.secret_key = "Secret Key"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

if not os.path.exists("sqlite///juegodb.db"):
    with app.app_context():
        db.create_all()

@app.context_processor
def utility_processor():
    def get_flashed_messages():
        return [message for message in flask.get_flashed_messages()]
    return dict(get_flashed_messages=get_flashed_messages)

@app.route("/")
def index():
    preguntas = db.session.query(Preguntas).all()
    jugador = db.session.query(Jugador).first()
    return render_template("index.html", preguntas=preguntas, jugador=jugador)

@app.route("/agregar_jugador", methods=["POST"])
def agregar_jugador():
    nombre = request.form["nombre"]
    jugador = Jugador(nombre=nombre, puntaje=0)
    db.session.add(jugador)
    db.session.commit()
    flash("Jugador agregado correctamente.")

    session["jugador_id"] = jugador.id  # Almacenar el ID del jugador en la sesión
    return redirect(url_for("index"))

@app.route("/update/<int:jugador_id>/<pregunta_id>", methods=["GET","POST"])
def update_juego(jugador_id, pregunta_id):
    jugador_id = session.get("jugador_id")
    jugador = db.session.query(Jugador).get(jugador_id)
    pregunta = db.session.query(Preguntas).filter_by(pregunta=pregunta_id).first()

    if request.method == "POST":
        respuesta = request.form["responder"]
        if respuesta == pregunta.correcta:
            flash("Respuesta CORRECTA")
            jugador.puntaje += 30
        else:
            flash("Respuesta Incorrecta")

        jugada = Jugada(jugador_id=jugador_id, pregunta_id=pregunta_id, puntaje=jugador.puntaje, respuesta=respuesta)
        db.session.add(jugada)
        db.session.commit()

        if jugador.puntaje >= 150:
            # Consulta para verificar si hay otros jugadores con puntaje >= 150
            empate = db.session.query(Jugador).filter(Jugador.puntaje >= 150, Jugador.id != jugador_id).first()
            if empate:
                flash(f"¡Empate con el jugador {empate.nombre}!")
            else:
                flash("*** FELICITACIONES, HAS GANADO EL JUEGO ***")
        return redirect(url_for("index"))

    return render_template("update.html", jugador_id=jugador_id, pregunta_id=pregunta_id)

if __name__ == "__main__":
    app.run(debug=True)
