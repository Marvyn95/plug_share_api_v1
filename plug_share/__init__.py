from flask import Flask
from flask_restful import Resource, Api
import pymongo
from pymongo import MongoClient
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# flask app and api instance creation
app = Flask(__name__)
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'plugshare_v1_12345'
jwt = JWTManager(app)

# mongoDB database connection
conn_string = "mongodb://Marvin:Marvollos95.@localhost:27017/"
cluster = pymongo.MongoClient(conn_string)
data_base = cluster["plug_share_01"]

from plug_share.resources import User, CommunityNeeds, Solutions, SolutionReviews
from plug_share.resources_2 import GeneralGeneral_1, GeneralGeneral_2,GeneralGeneral_3, Plugs
# adding all resources      
api.add_resource(User, "/users")
api.add_resource(CommunityNeeds, "/communityneeds")
api.add_resource(Solutions, "/solutions")
api.add_resource(GeneralGeneral_1, "/all_needs")
api.add_resource(GeneralGeneral_2, "/all_solutions")
api.add_resource(GeneralGeneral_3, "/need_info")
api.add_resource(SolutionReviews, "/reviews")
api.add_resource(Plugs, "/plugs")

