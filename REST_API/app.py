from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from pymysql import OperationalError

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
            'PublicationID': publication.PublicationID,  # ID de la publication
            'Title': publication.Title,                  # Titre de la publication
            'DOI': publication.DOI,                      # DOI de la publication
            'PublicationDate': publication.PublicationDate,  # Date de publication
            'Link': publication.Link,                    # Lien vers la publication
            'Abstract': publication.Abstract,            # Résumé de la publication
            'JournalID': publication.JournalID,          # ID du journal associé
            'Quartils': publication.Quartils             # Quartile du journal
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

@app.route('/publication_dates', methods=['GET'])
def get_publication_dates():
    # Récupérer uniquement la PublicationDate de toutes les publications
    publication_dates = db.session.query(Publication.PublicationDate).all()

    # Si aucune date de publication n'est trouvée
    if not publication_dates:
        return jsonify({'message': 'No publication dates found'}), 404

    # Formater les résultats dans un tableau de dates
    result = [date[0] for date in publication_dates]  # date[0] car chaque élément est un tuple

    return jsonify({'publication_dates': result}), 200

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

@app.route('/journal/<int:journal_id>', methods=['GET'])
def get_journal_by_id(journal_id):
    # Récupérer le journal en fonction de son ID
    journal = db.session.query(Journal).filter(Journal.JournalID == journal_id).first()

    if journal:
        # Retourner les informations du journal au format JSON
        return jsonify({
            'JournalID': journal.JournalID,
            'JournalMain': journal.JournalMain,
            'ISSN': journal.ISSN,
            'Quartils': journal.Quartils
        })
    else:
        # Si le journal n'est pas trouvé, renvoyer une erreur 404
        return jsonify({'message': 'Journal not found'}), 404

@app.route('/publication/<int:publication_id>', methods=['GET'])
def get_publication_by_id(publication_id):
    # Récupérer la publication en fonction de son ID
    publication = db.session.query(Publication).filter(Publication.PublicationID == publication_id).first()

    if publication:
        # Retourner les informations de la publication au format JSON
        return jsonify({
            'PublicationID': publication.PublicationID,
            'Title': publication.Title,
            'DOI': publication.DOI,
            'PublicationDate': publication.PublicationDate,
            'Link': publication.Link,
            'Abstract': publication.Abstract,
            'JournalID': publication.JournalID,
            'Quartils': publication.Quartils
        })
    else:
        # Si la publication n'est pas trouvée, renvoyer une erreur 404
        return jsonify({'message': 'Publication not found'}), 404

@app.route('/journal/<int:journal_id>/publications', methods=['GET'])
def get_publications_by_journal(journal_id):
    # Récupérer toutes les publications associées au journal par son ID
    publications = Publication.query.filter(Publication.JournalID == journal_id).all()

    # Si aucune publication n'est trouvée pour ce journal
    if not publications:
        return jsonify({'message': 'No publications found for this journal'}), 404

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

    return jsonify({'publications': result}), 200


@app.route('/quartils_by_journal/<int:journal_id>', methods=['GET'])
def get_quartils_by_journal(journal_id):
    # Récupérer les quartils associés au journal par son ID
    quartils = Quartil.query.filter(Quartil.id_journal == journal_id).all()

    # Si aucun quartil n'est trouvé pour ce journal
    if not quartils:
        return jsonify({'message': 'No quartils found for this journal'}), 404

    # Formater les résultats dans un tableau de données
    result = []
    for quartil in quartils:
        result.append({
            'QuartilID': quartil.QuartilID,
            'annee': quartil.annee,
            'quartil': quartil.quartil,
            'id_journal': quartil.id_journal
        })

    return jsonify({'quartils': result}), 200


if __name__ == '__main__':
    app.run(debug=True)
