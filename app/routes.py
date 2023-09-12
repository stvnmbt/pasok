from app import app
from flask import Flask, render_template, url_for

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/home")
def home():
    return render_template("home.html")