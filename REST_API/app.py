from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from pymysql import OperationalError


app = Flask(__name__)

# Configuration de la chaîne de connexion pour SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://mohammed:mohammed@localhost:3366/PublicationsDataWarehouse'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Désactive la gestion des modifications

# Initialisation de l'instance SQLAlchemy
db = SQLAlchemy(app)

class Journal(db.Model):
    __tablename__ = 'Journal'  # Nom de la table dans la base de données
    JournalID = db.Column(db.Integer, primary_key=True)
    JournalMain = db.Column(db.String(255), nullable=False)
    ISSN = db.Column(db.String(50), nullable=True)
    Quartils = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Journal {self.JournalMain}>"

class Publication(db.Model):
    __tablename__ = 'Publications'  # Nom de la table dans la base de données
    PublicationID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    DOI = db.Column(db.String(100), nullable=True)
    PublicationDate = db.Column(db.Date, nullable=True)
    Link = db.Column(db.String(255), nullable=True)
    Abstract = db.Column(db.Text, nullable=True)
    JournalID = db.Column(db.Integer, db.ForeignKey('Journal.JournalID'), nullable=True)  # Clé étrangère vers Journal
    Quartils = db.Column(db.String(50), nullable=True)

    journal = db.relationship('Journal', backref=db.backref('publications', lazy=True))  # Relation avec Journal

    def __repr__(self):
        return f"<Publication {self.Title}>"

# Définir le modèle pour la table Quartils
class Quartil(db.Model):
    __tablename__ = 'Quartils'  # Nom de la table dans la base de données
    QuartilID = db.Column(db.Integer, primary_key=True)
    annee = db.Column(db.String(4), nullable=False)
    quartil = db.Column(db.String(255), nullable=True)
    id_journal = db.Column(db.Integer, db.ForeignKey('Journal.JournalID'), nullable=True)  # Clé étrangère vers Journal

    journal = db.relationship('Journal', backref=db.backref('quartils', lazy=True))  # Relation avec Journal

    def __repr__(self):
        return f"<Quartil {self.quartil} ({self.annee})>"

class Author(db.Model):
    __tablename__ = 'Authors'  # Nom de la table dans la base de données
    AuthorID = db.Column(db.Integer, primary_key=True)
    AuthorName = db.Column(db.String(100), nullable=False)
    Affiliation = db.Column(db.String(255), nullable=True)
    Country = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Author {self.AuthorName}>"

# Route pour obtenir les auteurs
@app.route('/authors', methods=['GET'])
def get_authors():
    # Récupérer tous les auteurs de la base de données
    authors = Author.query.all()

    # Formater les résultats dans un dictionnaire
    result = []
    for author in authors:
        result.append({
            'AuthorID': author.AuthorID,
            'AuthorName': author.AuthorName,
            'Affiliation': author.Affiliation,
            'Country': author.Country
        })

    return {"authors": result}, 200

# Route pour obtenir les quartils
@app.route('/quartils', methods=['GET'])
def get_quartils():
    # Récupérer tous les quartils de la base de données
    quartils = Quartil.query.all()

    # Formater les résultats dans un dictionnaire
    result = []
    for quartil in quartils:
        result.append({
            'QuartilID': quartil.QuartilID,
            'annee': quartil.annee,
            'quartil': quartil.quartil,
            'id_journal': quartil.id_journal
        })

    return {"quartils": result}, 200

@app.route('/test_connection')
def test_connection():
    try:
        # Essayer de se connecter à la base de données en effectuant une requête
        with app.app_context():
            db.engine.connect()  # Tentative de connexion à la base de données
        return "Connection to the database is successful!", 200  # Message de succès
    except OperationalError as e:
        # Si la connexion échoue, afficher l'erreur
        return f"Error connecting to the database: {str(e)}", 500

@app.route('/journals', methods=['GET'])
def get_journals():
    # Récupérer tous les journaux de la base de données
    journals = Journal.query.all()

    # Formater les résultats dans un dictionnaire
    result = []
    for journal in journals:
        result.append({
            'JournalID': journal.JournalID,
            'JournalMain': journal.JournalMain,
            'ISSN': journal.ISSN,
            'Quartils': journal.Quartils
        })

    return {"journals": result}, 200

@app.route('/publications', methods=['GET'])
def get_publications():
    # Récupérer toutes les publications de la base de données
    publications = Publication.query.all()

    # Formater les résultats dans un dictionnaire
    result = []
    for publication in publications:
        result.append({
            'PublicationID': publication.PublicationID,
            'Title': publication.Title,
            'DOI': publication.DOI,
            'PublicationDate': publication.PublicationDate,
            'Link': publication.Link,
            'Abstract': publication.Abstract,
            'JournalID': publication.JournalID,
            'Quartils': publication.Quartils
        })

    return {"publications": result}, 200


@app.route('/publications_by_journal', methods=['GET'])
def publications_by_journal():
    # Récupérer le nombre de publications par journal
    result = db.session.query(Journal.JournalMain, db.func.count(Publication.PublicationID)).join(Publication).group_by(
        Journal.JournalMain).all()

    # Structurer les données pour l'affichage
    data = [{'Journal': row[0], 'Publications': row[1]} for row in result]

    return jsonify(data)


@app.route('/journals_by_quartil_and_annee', methods=['GET'])
def journals_by_quartil_and_annee():
    # Récupérer les journaux, quartils et années associés
    result = db.session.query(
        Journal.JournalMain,
        Quartil.quartil,
        Quartil.annee
    ).join(
        Quartil,
        Journal.JournalID == Quartil.id_journal
    ).all()

    # Structurer les données pour l'affichage
    data = [
        {'Journal': row[0], 'Quartil': row[1], 'Annee': row[2]}
        for row in result
    ]

    return jsonify(data)




if __name__ == '__main__':
    app.run(debug=True)
