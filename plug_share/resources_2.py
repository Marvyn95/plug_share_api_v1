from flask_restful import Resource, Api, reqparse
import bcrypt
from flask import jsonify
from plug_share import data_base, jwt
from bson import ObjectId
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime

class GeneralGeneral_1(Resource):
    #gets all needs
    def get(self):
        try:
            all_needs = data_base.needs.find()
            all_needs = list(all_needs)
            count = 0
            for item in all_needs:
                item["_id"] = str(item["_id"])
                count = count +1
            
            return{
                "count": count,
                "top_needs": all_needs
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

class GeneralGeneral_2(Resource):
    #gets all solutions
    def get(self):
        try:
            all_solutions = data_base.solutions.find()
            all_solutions = list(all_solutions)
            count = 0
            for item in all_solutions:
                item["_id"] = str(item["_id"])
                count = count +1
            
            return{
                "count": count,
                "top_needs": all_solutions
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

# get need info parser
need_info_parser = reqparse.RequestParser()
need_info_parser.add_argument("user_id", location="args", type=str)
need_info_parser.add_argument("need_id", location="args", type=str)

# get all need info
class GeneralGeneral_3(Resource):
    def get(self):
        try:
            args = need_info_parser.parse_args()
            need_info = data_base.needs.find_one({"_id": ObjectId(args["need_id"])})

            array_01 = []
            for item in need_info["solutions_submitted"]:
                nd = data_base.solutions.find_one({"_id": ObjectId(item)})
                nd["_id"] = str(nd["_id"])
                array_01.append(nd)
            need_info["solutions_submitted"] = array_01
            need_info["_id"] = str(need_info["_id"])

            return {
                "status": True,
                "need_info": need_info
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

#getting community plugs 
class Plugs(Resource):
    def get(self):
        try:
            all_solutions = data_base.solutions.find()
            reviewed_solutions = []
            for item in all_solutions:
                item["_id"] = str(item["_id"])
                if len(item["reviews"]) != 0:
                    total_stars = 0
                    for review in item["reviews"]:
                        total_stars += review["solution_rating"]
                    item["overall_star_rating"] = ((total_stars)/(5*(len(item["reviews"]))))*5
                    reviewed_solutions.append(item)

            plugs = []
            count = 0
            for j in reviewed_solutions:
                if j["overall_star_rating"] >= 3:
                    plugs.append(j)
                    count += 0
            
            plugs.sort(key=lambda x: x["overall_star_rating"], reverse=True)
            
            return {
                "count": count,
                "plugs": plugs
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }