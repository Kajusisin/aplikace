"""Modely pro odkazy, informace a soubory."""

from db_config import db
from datetime import datetime

class Odkaz(db.Model):
    __tablename__ = 'odkazy'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    kategorie = db.Column(db.String(100), nullable=False)
    datum_vytvoreni = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Odkaz {self.nazev} ({self.kategorie})>"

class Informace(db.Model):
    __tablename__ = 'informace'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    datum = db.Column(db.String(20), nullable=False)  # Ve formátu DD.MM.YYYY
    datum_vytvoreni = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Informace {self.text[:20]}... ({self.datum})>"

class Soubor(db.Model):
    __tablename__ = 'soubory'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    velikost = db.Column(db.Integer)  # Velikost v bajtech
    typ_souboru = db.Column(db.String(50))  # Např. pdf, docx
    datum_nahrani = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Soubor {self.nazev}>"
