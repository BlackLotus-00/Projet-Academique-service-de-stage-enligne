
from flask import Flask,render_template, url_for,jsonify, request,flash,redirect,session,make_response
import os
from werkzeug.utils import secure_filename
import EasyOCR as eOcr
import json
from passlib.hash import pbkdf2_sha256
from flask_pymongo import PyMongo 
from bson import ObjectId
import pwdrandom
from flask_mail import Mail, Message


# Create a directory in a known location to save files to.
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MONGO_DBNAME'] = 'Projet_2'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Project_2'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'e.stage.enim@gmail.com'
app.config['MAIL_PASSWORD'] = '1998KHKHKHKH'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mongo = PyMongo(app)
Amail = Mail(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


"""Check if match """
def check_if_match(doc, Xs):
   
   test=0
   lent = len(Xs)
   for x in Xs:
      if x in doc:
         test+=1
   return test / lent * 100


# @app.route('/convention')
# def Convention():

@app.route('/')
def index():
    if session.get('Admin'):
        return redirect(url_for('indexAdmin'))
    if session.get('logged_in') == True:
       username = session['username'] 
       Orgs = mongo.db.NewOrg
       NewOrg = Orgs.find_one({'user._id': ObjectId(session['id'])})
       if NewOrg:
            return render_template("index.html",username = username,Org = NewOrg, Orgfound = True)
       return render_template("index.html",username = username,Org = NewOrg, Orgfound = False)
    return render_template("index.html",username = 'Not Found')


@app.get('/indexAdmin')
def indexAdmin():
    if session['Admin'] : 
        NewOrgs = mongo.db.NewOrg
        Orgs = NewOrgs.find()
        u_sers = mongo.db.users
        users = u_sers.find()
        
        return render_template("indexAdmin.html",users = users,Orgs = Orgs)
    return render_template('404.html')

@app.route('/document',methods=["POST","GET"])
def document():
    if session.get('logged_in') == True:
       username = session['username'] 
    else:
       username = 'Not Found'

    
    if request.method == "POST":
        
        file = request.files['documentImage']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            document_name = eOcr.get_jpg(file.read(), file.filename)
            document_text = eOcr.easyocr_read(document_name)
            #Test inputes :
            doc = mongo.db.Doctest
            if(request.form['radio']=='FA'):
                a = " Fiche d'appréciation "
                FApp = doc.find_one({'type':'FA'})
                y = check_if_match(document_text, FApp['Fichier_Appreciation'].split())
            elif(request.form['radio']=='ATS'):
                a = " attestation de stage "
                FApp = doc.find_one({'type':'ATS'})
                y = check_if_match(document_text, FApp['Attestation'].split())
            elif(request.form['radio']=='CONV'):
                a = " convention de stage "
                FApp = doc.find_one({'type':'CONV'})
                y = check_if_match(document_text, FApp['Convention'].split())
            else:
                y = 0
            b='0'
            if y >=60:
                ocrk = "Votre" + a + "est bien enregistrée"
                b='1'
            else:
                ocrk = "Le fichier non valide"
                
            return render_template("document.html", filenew = filename, ocrK = ocrk, b=b,username = username)
    return render_template("document.html",username = username)


##Ajouter un nouveau utilisateur 
@app.route('/document/NouveauStage', methods=['POST', 'GET'])
def addStage():
    if request.method == 'POST':
        NewOrg = mongo.db.NewOrg
        users = mongo.db.users
        existing_user = NewOrg.find_one({'user':ObjectId(session['id']), 'status':True})
        user = users.find_one({'_id':ObjectId(session['id'])})
        if existing_user is None :
            NewOrg.insert_one({'user': user,
            'status':True,
            'orgName': request.form['organisme'],
            'adresseOrg' : request.form['adresseOrg'],
            'VilleOrg' : request.form['VilleOrg'],
            'DateDebut' : request.form['DateDebut'],
            'Datefin' : request.form['Datefin'],
            'AdresseEnc' : request.form['AdresseEnc'],
            'category' : request.form['category']})
            return redirect(url_for('index'))
        
    return redirect(url_for('document'))




@app.route('/document/<index>', methods=['POST','GET'])
def GetDocument(index):
    if session.get('logged_in') == True:
        if request.method == 'GET':
            if index == 'convention':
                #Insertion des données:
                return render_template('login.html')
            if index == 'a':
                return redirect(url_for('document'))
    else :
            return render_template('index.html')



#___________________________Generate HTML CONVENTION _____________________________#
@app.route('/convention')
def conv():
    x = ObjectId(session['id'])
    Orgs = mongo.db.NewOrg
    st = Orgs.find_one({'user._id':x})
    if st:
        Prenom =  st['user']['Nom'] #Nom et n'ont pas le prenom
        NOM = st['user']['Prenom']
        CIN = st['user']['CIN']
        Filiere = st['user']['Filière/option']
        DateDebut = st['DateDebut']
        DateFin = st['Datefin']
        Organisme = st['orgName']
        VilleOrganisme = st['VilleOrg']
        addressOrg = st['adresseOrg']
        from datetime import date
        today = date.today()
        # dd/mm/YY
        DateF =today.strftime("%d/%m/%Y")
        return render_template('Convention.html', Prenom = Prenom, NOM = NOM, CIN=CIN, Filiere=Filiere, DateDebut=DateDebut, DateFin=DateFin,Organisme=Organisme,VilleOrganisme=VilleOrganisme,addressOrg=addressOrg, DateF=DateF)
    return redirect(url_for('index'))










#_______________________________________Login Inscription _____________________________________
###_________________________________First Login______________
@app.route('/loginValid', methods=['POST', 'GET'])
def firstTimeLogin():
    if request.method == "POST":
        if request.form['mdpNew2'] == request.form['mdpNew']:
            users = mongo.db.users
            passwd = request.form['mdpNew']
            hashpass = pbkdf2_sha256.hash(passwd)
            users.update_one({'_id':ObjectId(request.form['OID'])},{"$set" : {'password' : hashpass, 'statut':'NoLogin'}})
            return redirect(url_for('login'))
        return "Invalide New password/retry Password"
    return redirect(url_for('index'))
       

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'name':request.form['username']})
        #json.dumps(login_user)
        if(login_user ):
            k = str(login_user['_id'])
            
            if  pbkdf2_sha256.verify(request.form['pass'], login_user['password']):
                if(login_user['statut']!='login'):
                    session['id'] = k
                    session['username'] = request.form['username']
                    session['logged_in'] = True
                    print(session['id'])
                    return redirect(url_for('index'))
                return render_template('valide_login.html', Prenom=login_user['Prenom'],Nom=login_user['Nom'], logId=login_user['_id'])
                

            return 'Invalid username/password combination'


        return 'Invalid username/password combination'

    return render_template('login.html')



@app.route('/logout')
def logout():
    
    session['logged_in'] = False
    session['Admin'] = False
    session.pop('username', None) 
    session.pop('id', None) 
    return redirect(url_for('index'))

@app.route('/Admin', methods=['POST','GET'])
def admin():
    if request.method =='POST':
        Admin = mongo.db.Admin
        login_admin = Admin.find_one({'name':request.form['username']})
        if(login_admin ):
           
            if  pbkdf2_sha256.verify(request.form['pass'], login_admin['password']):
                session['username'] = request.form['username']
                session['logged_in'] = True
                session['Admin'] = True
                return redirect(url_for('indexAdmin'))
        else:
            return render_template('404.html')
    
    return render_template('loginAdmin.html')




@app.route('/register', methods=['POST', 'GET'])
def register():
    #tu dois vérifier s'il s'agit d'un adim ou non
    users = mongo.db.users
    users_com = users.find()

    if request.method == 'POST':
            
            ########Pour envoyer par mail le mot de passe:
            users_updated = users.find({'password':''})
            users_dict = {}
            for user in users_updated:
                passwd = pwdrandom.randomPwd(16)
                hashpass = pbkdf2_sha256.hash(passwd)
                users.update_one({'_id':user['_id']},{"$set" : {'password' : hashpass, 'statut':'login'}})
                users_dict.update({user['name']:passwd})
                print('==========================> ', user['name'])
                #______________L'envoi des Emails ________________________#
                for mail in users_dict:
                    msg = Message("Login pour accéder à l'application des Stages", sender =   'mezgour.yassine@gmail.com', recipients = [mail])
                    msg.html = "<p><center><img src='../static/images//gh.png' alt='' ></center></p><b>Bonjour</b><br> voici le lien pour accéder à l'application des Stages <a href='http://127.0.0.1:5000/login'>test.enim.ac.ma</a></br>login:<br><b>Utilisateur:</b>" + mail + "<br><b>Mot de passe:</b>" + users_dict[mail] +"<br>Cordialement"
                    Amail.send(msg)
            print('=============================================================>',users_dict)
            return render_template('register.html', users=users_com)
    return render_template('register.html', users=users_com)


if __name__ == "__main__":
    app.secret_key = 'mysecret'
    app.run(debug=True)