from flask import Flask, request, jsonify,render_template,url_for
from flask_cors import CORS
from flask_pymongo import PyMongo
import os
from PandM.Backend.MainCode import BookMusicRecommender
from PandM.Backend.MainCode import MongoCalls

base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
template_dir=os.path.join(base_dir,'Frontend','templates')
static_dir=os.path.join(base_dir,'Frontend','static')
app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)
CORS(app)  # Allow requests from frontend

# # Connect to MongoDB
# client = pymongo.MongoClient("mongodb://localhost:27017/")
# db = client["ProseMelody"]  # Database name
# users_collection = db["users"]  # Collection name

# app=Flask(__name__)
# app.config["MONGO_URI"]=os.getenv("MONGO_URI")
# db=PyMongo(app).db

maincall=BookMusicRecommender()
storecall=MongoCalls()
def datain(title,platform):
    if platform=='spotify' and title!=None:
        d=[title,maincall.s_stack[-1],'spotify',maincall.final_music[maincall.s]]
    else:
        d=[title,maincall.y_stack[-1],'youtube',maincall.final_music[maincall.y]]
    return d


@app.route('/')
def index():
    return render_template("index.html")

@app.route("/signup")
def signuppage():
    return render_template("signup.html")

# Route for user login
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/mainpg')
def mainpg():
    return render_template('mainpg.html')


@app.route("/Enter", methods=["POST"])
def submit():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    user_id=storecall.get_user_by_email(email,password)
    # Check if user exists
    if user_id:
        maincall.current_user=user_id
        print("entering:",maincall.current_user)
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401
    
@app.route("/newUser",methods=['POST'])
def newUser():
    data=request.json
    email=data.get('email')
    password=data.get('password')
    check=storecall.get_user_by_email(email,password)
    if check:
        return jsonify({'message':'User already exists.Go to Login!'})
    else:
        storecall.add_user(data)
        return jsonify({'message':"Account created.Login to Enter!"})


@app.route("/bookEntry",methods=['POST'])
def bookEntry():
    data=request.json
    title=data.get('book')
    instrument=data.get('instrument')
    language=data.get('language')
    maincall.title=title
    check=maincall.bookSearch(title)
    if check!=True:
        jsonify({"message":check})
    result={}
    print("the current title:",maincall.title)
    result['spotify']=maincall.forward("spotify",instrument,language)
    d=datain(maincall.title,'spotify')
    print("the data entering in db is :",d)
    newdata={'user_id':maincall.current_user,'Recents':d}
    storecall.add_recent_playlist(newdata)
    result['youtube']=maincall.forward("youtube",instrument,language)
    d=datain(maincall.title,'youtube')
    newdata={'user_id':maincall.current_user,'Recents':d}
    storecall.add_recent_playlist(newdata)
    return jsonify(result)



@app.route("/forward",methods=['POST'])
def forward():
    data=request.json
    platform=data.get("platform")
    instrument=data.get('instrument')
    language=data.get("language")
    result=maincall.forward(platform,instrument,language)
    if result=='End of playlist':
        return jsonify({"message",result})
    d=datain(maincall.title,platform)
    newdata={'user_id':maincall.current_user,'Recents':d}
    storecall.add_recent_playlist(newdata)
    return jsonify(result)

@app.route("/previous",methods=['POST'])
def previous():
    data=request.json
    platform=data.get("platform")
    instrument=data.get('instrument')
    language=data.get("language")
    result=maincall.previous(platform)
    if result==-1:
        return jsonify({"message":"it's the begining"})
    final={'platform':platform,'link':result}
    # print(final)
    return jsonify(final)

@app.route("/fromRec",methods=['POST'])
def fromRec():
    data=request.json
    genre=data.get('genre')
    platform=data.get('platform')
    result=maincall.OnSpot(genre,platform)
    if result==-1:
        return jsonify({"message":"internal error occured"})
    final={'playlistUrl':result,'platform':platform}
    # print("from rec:",final)
    return jsonify(final)

@app.route("/basicRec")
def basicRec():
    print("user:",maincall.current_user)
    result=maincall.basic_recommendation(maincall.current_user)
    if result==[]:
        return jsonify({"message":"u r the first user"})
    return jsonify(result)

@app.route("/addFavourite", methods=['PUT'])
def addFavourite():
    try:
        data = request.json
        print("Received data:", data)

        platform = data.get('platform')
        genre = data.get('genre')
        link = data.get('link')

        if link is None and genre is None:
            d = datain(maincall.title, platform)
        else:
            d = ['Recommendations', link, platform, genre]

        result = {'user_id': maincall.current_user, 'Favourites': d}
        storecall.add_favorite_playlist(result)

        return jsonify({'message': "done"})

    except Exception as e:
        print("Error in /addFavourite:", str(e))
        return jsonify({"error": "Internal Server Error"}), 500



@app.route("/recents")
def recents():
    print(maincall.current_user)
    dictionary=storecall.get_recent_playlists_by_user_id(maincall.current_user)
    return dictionary

@app.route("/favourite")
def favourite():
    print("user:",maincall.current_user)
    dictionary=storecall.get_favorite_playlists_by_user_id(maincall.current_user)
    return dictionary

@app.route("/profile")
def profile():
    details=storecall.get_user(maincall.current_user)
    # print(details)
    return details



# Run the server
if __name__ == "__main__":
    app.run(debug=True)
