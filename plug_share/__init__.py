from flask import Flask
from flask_restful import Api
import pymongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json, os

base_dir = os.path.dirname(os.path.abspath("run.py"))
config_path = os.path.join(base_dir,"config.json")

with open(config_path, "r") as file:
    config = json.load(file)

# flask app and api instance creation
app = Flask(__name__)
api = Api(app)
app.config['JWT_SECRET_KEY'] = config.get("JWT_SECRET_KEY")
jwt = JWTManager(app)

# mongoDB database connection
conn_string = config.get("plugshare_mongodb_conn_string")
cluster = pymongo.MongoClient(conn_string)
data_base = cluster["plug_share_01"]

from plug_share.resources import User, CommunityNeeds, Solutions, SolutionReviews, Endorsements
from plug_share.resources_2 import GeneralGeneral_1, GeneralGeneral_2,GeneralGeneral_3, Plugs, Alternatives
# adding all resources      
api.add_resource(User, "/users")
api.add_resource(CommunityNeeds, "/communityneeds")
api.add_resource(Solutions, "/solutions")
api.add_resource(GeneralGeneral_1, "/all_needs")
api.add_resource(GeneralGeneral_2, "/all_solutions")
api.add_resource(GeneralGeneral_3, "/need_info")
api.add_resource(SolutionReviews, "/reviews")
api.add_resource(Plugs, "/plugs")
api.add_resource(Endorsements, "/endorsements")
api.add_resource(Alternatives, "/alternatives")