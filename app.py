from flask import Flask, request, render_template, session, redirect, flash, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import requests


def get_meme():
    url = "https://meme-api.com/gimme"

    response = requests.get(url)
    data = response.json()

    return data['preview'][-1]

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs_db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SESSION_PERMAMENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)



class Blogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    content = db.Column(db.String(2500), nullable=False)
    upload_date = db.Column(db.Date, default = datetime.utcnow)
    editor_id = db.Column(db.Integer, db.ForeignKey('editors.id'))
    image_name = db.Column(db.String(40), nullable=False)

    def __init__(self,title,category,content,editor_id, image_name = "Unnamed"):
        self.title = title
        self.category = category
        self.content = content
        self.editor_id = editor_id
        self.image_name = image_name

    def __str__(self):
        return f'Blog title:{self.title}; Category: {self.category}\ncontent: {self.content}'
    
class Editors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(40), nullable=False)
    mail = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    blogs = db.relationship('Blogs', backref='editor')
    
    def __init__(self, fullname, mail, password):
        self.fullname = fullname
        self.mail = mail
        self.password = password
    
    


@app.route('/',methods=['POST', 'GET'])
def index():
    global counter
    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        content = request.form.get('content')
        image = request.files.get('image')

        blog = Blogs(title, category, content, session['user'].id)

        db.session.add(blog)
        db.session.commit()
        
        filename = secure_filename(image.filename)
        file_extension = os.path.splitext(filename)[1]
        new_filename = str(blog.id) + file_extension
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        image.save(filepath)
    
        blog.image_name = new_filename
        db.session.commit()
        flash('Your Blog Has Been Added', 'info')
        
    blogs = Blogs.query.all()
                
    return render_template('index.html', blogs=blogs)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html', meme_pic = get_meme())

@app.route('/edit', methods = ['POST', 'GET'])
def edit():
    if request.method == 'POST':
        mail = request.form.get('mail')
        password = request.form.get('password')
        editor = Editors.query.filter_by(mail = mail, password=password).first()
        
        if editor == None:
            return redirect('/signin')
        
        session['user'] = editor
        
        return render_template('editors.html', blogs = Blogs.query.filter_by(editor_id = editor.id))
    
    elif not session.get('user'):
        return redirect('/signin')
    
    else:
        return render_template('editors.html', blogs = Blogs.query.filter_by(editor_id = session['user'].id))

@app.route('/signin', methods = ['POST', 'GET'])
def signin():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        mail = request.form.get("mail")
        password = request.form.get("password")
        editor = Editors(fullname, mail,password)
        db.session.add(editor)
        db.session.commit()
    return render_template('signin.html')

@app.route('/signup', methods=["POST", "GET"])
def signup():
    flash("You have registered", "info")
    return render_template('signup.html')

@app.route('/suggested')
def suggested():
    category = request.args.get('category')
    blogs = Blogs.query.filter_by(category = category).all()
    return render_template('suggested.html', blogs = blogs)

@app.route('/editors1', methods = ['POST', 'GET'])
def editors1():
    if request.method =='POST':
        get_order = request.form.get('order')
        object = Blogs.query.get(get_order)
        db.session.delete(object)
        db.session.commit()
    if not session.get('user'):
        return redirect('/signin')
    else:
        return render_template('editors1.html', blogs = Blogs.query.filter_by(editor_id = session['user'].id))
    

@app.route('/read', methods = ["POST", "GET"])
def read():
    id = request.form.get('id')
    object = Blogs.query.get(id)
    editor = Editors.query.get(object.editor_id)
    return render_template('read.html', title = object.title, content = object.content, image_name = object.image_name, editor = editor.fullname)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect("/signin")

if __name__=="__main__":
    app.run(debug=True)
