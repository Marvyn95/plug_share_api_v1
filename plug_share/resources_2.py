from flask_restful import Resource, reqparse
from flask import jsonify
from plug_share import data_base, jwt
from bson import ObjectId
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import secrets

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
                "all_needs": all_needs
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
                "all_solutions": all_solutions
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
need_info_parser.add_argument("sub_category_id", location="args", type=str)

# get all need info
class GeneralGeneral_3(Resource):
    def get(self):
        args = need_info_parser.parse_args()
        category = data_base.needs.find_one({"_id": ObjectId(args["sub_category_id"])})
        for x in category["votes"]:
            if x["need_id"] == args["need_id"]:
                poster_info = data_base.users.find_one({"_id": ObjectId(x["user_id"])})
                for y in poster_info["needs"]:
                    if y["need_id"] == args["need_id"]:
                        need = y
                        need["need_poster_id"] = str(poster_info["_id"])
                        need["need_poster_name"] = poster_info["user_name"]
                        need["need_poster_email"] = poster_info["email"]
        
        #finding need solutions and added them to return object
        need_solutions = []
        for k in category["solutions_submitted"]:
            if k["need_id"] == args["need_id"]:
                sol = data_base.solutions.find_one({"_id": ObjectId(k["solution_id"])})
                sol["_id"] = str(sol["_id"])

                #getting and adding solution poster key info
                sol_poster = data_base.users.find_one({"_id": ObjectId(sol["user_id"])})
                sol_poster_key_info = {
                    "id": str(sol_poster["_id"]),
                    "name": sol_poster["user_name"],
                    "email": sol_poster["email"],
                    "stars": sol_poster["stars"],
                    "points": sol_poster["points"]
                }
                sol["solution_poster_info"] = sol_poster_key_info
                need_solutions.append(sol)
        need["solutions_posted"] = need_solutions

        return {
            "status": True,
            "need_info": need
        }


#getting community plugs 
class Plugs(Resource):
    def get(self):
        try:
            all_solutions = data_base.solutions.find()
            reviewed_solutions = []
            for item in all_solutions:
                item["_id"] = str(item["_id"])
                if len(item["endorsements"] != 0):
                    reviewed_solutions.append(item)
           
            reviewed_solutions.sort(key=lambda x: x["points"], reverse=True)
            
            return {
                "plugs": reviewed_solutions[:30]
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }
        
#parser for getting solution alternatives
get_alternatives_parser = reqparse.RequestParser()
get_alternatives_parser.add_argument("user_id", location="args", type=str)
get_alternatives_parser.add_argument("solution_id", location="args", type=str)

#getting all alternatives to solution
class Alternatives(Resource):
    def get(self):
        args = get_alternatives_parser.parse_args()
        alternatives = data_base.solutions.find_one({"_id": ObjectId(args["solution_id"])})["alternative_solutions"]
        detailed_alternatives = []
        for item in alternatives:
            alternative_info = data_base.solutions.find_one({"_id": ObjectId(item["alternative_solution_id"])})
            alternative_info["_id"] = str(alternative_info["_id"])

            #getting poster's info and adding it to return odject
            poster_info = data_base.users.find_one({"_id": ObjectId(alternative_info["user_id"])})
            alternative_info["poster_info"] = {
                "poster_name": poster_info["user_name"],
                "poster_email": poster_info["email"],
                "poster_stars": poster_info["stars"],
                "poster_points": poster_info["points"]
            }
            
            detailed_alternatives.append(alternative_info)

        return {
            "status": True,
            "alternative_solutions": detailed_alternatives
        }
    


#parser for upvoting or removing vote
need_vote_parser = reqparse.RequestParser()
need_vote_parser.add_argument("user_id", location="args", type=str) 
need_vote_parser.add_argument("need_owner_id", location="args", type=str) 
need_vote_parser.add_argument("need_id", location="args", type=str)

#upvoting and downvoting needs by users
class NeedVotes(Resource):
    def post(self):
        args = need_vote_parser.parse_args()

        #getting user info
        user_01 = data_base.users.find_one({"_id": ObjectId(args["user_id"])})
        
        # getting upvoted need info
        need_owner_info = data_base.users.find_one({"_id": ObjectId(args["need_owner_id"])})
        for item in need_owner_info["needs"]:
            if item["need_id"] == args["need_id"]:
                need_info = item
                break
        
        # adding need to user profile
        new_need_id = secrets.token_hex(16)
        if len(user_01["needs"]) < 3:
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"needs": {
                "need_id": new_need_id,
                "sub_category_id": need_info["sub_category_id"],
                "location": need_info["location"],
                "purpose": need_info["purpose"]
            }}})

            data_base.needs.update_one({"_id": ObjectId(need_info["sub_category_id"])}, {"$push": {"votes": {
                "user_id": args["user_id"],
                "need_id": new_need_id
            }}})

            return {
                "status": True,
                "message": "You Have Upvoted This Need Succesfully and It Has Been Added To Your List Of Needs"
            }
        else:
            return {
                "status": False,
                "message": "Your List of Needs is Already Full! :)"
            }

