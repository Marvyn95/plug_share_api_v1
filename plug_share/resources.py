from flask_restful import Resource, Api, reqparse
import bcrypt
from flask import jsonify
from plug_share import data_base, jwt
from bson import ObjectId
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime

# new user arguments parser
new_user_parser = reqparse.RequestParser()
new_user_parser.add_argument("user_name", type=str, required=True, location="form")
new_user_parser.add_argument("email", required=True, location="form")
new_user_parser.add_argument("password", required=True, location="form")
new_user_parser.add_argument("confirm_password", required=True, location="form")

# existing user parser
existing_user_parser = reqparse.RequestParser()
existing_user_parser.add_argument('user_id', type=str, location='args', required=True)

# signing in parser
signin_parser = reqparse.RequestParser()
signin_parser.add_argument("email", type=str, required=True, location="form")
signin_parser.add_argument("password", type=str, required=True, location="form")

# edit user details parser
edit_user_details_parser = reqparse.RequestParser()
edit_user_details_parser.add_argument("user_name", type=str, required=True, location="form")
edit_user_details_parser.add_argument("email", required=True, location="form")
edit_user_details_parser.add_argument("user_id", required=True, location="args")

class User(Resource):
    # creating a new user / signing up
    def put(self):
        try:
            args=new_user_parser.parse_args()
            if data_base.users.find_one({"email": args["email"]}) != None:
                return {
                    "status": False,
                    "message": "Account Already Exists!"
                }
            if args["password"] == args["confirm_password"]:
                hashed_password = bcrypt.hashpw(args["password"].encode("utf-8"), bcrypt.gensalt())
                new_user = {
                    "user_name": args["user_name"],
                    "email": args["email"],
                    "password": hashed_password.decode("utf-8"),
                    "needs": [],
                    "solutions_submitted": [],
                    "solutions_rated": [],
                    "role": "user",
                    "badges": []
                }
                data_base.users.insert_one(new_user)
                return {
                    "status": True,
                    "user_name": args["user_name"],
                    "email": args["email"],
                    "message": "Account Created Successfuly :)"
                }
            else:
                return {
                    "status": False,
                    "message": "Account Creation Not Successful, Check Email and Password"
                }

        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }


    # getting user page info
    def get(self):
        try:
            args = existing_user_parser.parse_args()
            user_01 = data_base.users.find_one({"_id": ObjectId(args["user_id"])})
            user_01["_id"] = str(user_01["_id"])
            for i in user_01["needs"]:
                i["_id"] = str(i["_id"]) 
            user_01.pop("password")
            return user_01
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }
    
    # signing in
    def post(self):
        try:
            args = signin_parser.parse_args()
            user_01 = data_base.users.find_one({"email": args["email"]})
            if user_01 != None:
                if bcrypt.checkpw(args["password"].encode("utf-8"), user_01["password"].encode("utf-8")):
                    access_token = create_access_token(identity=str(user_01["_id"]))
                    return {
                        "status": True,
                        "message": "Login Successful",
                        "user_name": user_01["user_name"], 
                        "user_email": user_01["email"],
                        "access_token": access_token
                    }
                else:
                    return {
                        "status": False,
                        "message": "Login Unsuccessful!, Check Password"
                    }
            else:
                return {
                    "status": False,
                    "message": "Login Unsuccessful!, Check Email"
                }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }
    
    #edit user_name and email
    # @jwt_required()
    def patch(self):
        try:
            args = edit_user_details_parser.parse_args()
            user_01 = data_base.users.find_one({"email": args["email"]})

            if user_01 != None and user_01["_id"] != ObjectId(args["user_id"]):
                return {
                    "status": False,
                    "message": "Email Already Exists!, Perhaps Try Another :("
                }
            else:
                data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$set": {"user_name": args["user_name"], "email": args["email"]}})
                return {
                "status": True,
                "message": "Update Successful!:)"
                }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

# parser for adding/voting needs to list
needs_selection_parser = reqparse.RequestParser()
needs_selection_parser.add_argument("need_1", type = str, location = "form")
needs_selection_parser.add_argument("need_2", type = str, location = "form")
needs_selection_parser.add_argument("need_3", type = str, location = "form")
needs_selection_parser.add_argument("need_4", type = str, location = "form")
needs_selection_parser.add_argument("user_id", type = str, location = "args")

class CommunityNeeds(Resource):
    # getting top needs 
    def get(self):
        try:
            top_needs = data_base.needs.find({"votes": {"$gt": 0}}).sort("votes", -1).limit(30)
            top_needs = list(top_needs)
            count = 0
            for item in top_needs:
                item["_id"] = str(item["_id"])
                count = count +1
            
            return{
                "count": count,
                "top_needs": top_needs,
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

    # adding needs to profile
    # @jwt_required()
    def post(self):
        try:
            args = needs_selection_parser.parse_args()
            user_01 = data_base.users.find_one({"_id": ObjectId(args["user_id"])})

            if len(user_01["needs"]) == 0:
                #updating votes for the needs selected
                data_base.needs.update_one({"_id": ObjectId(args["need_1"])}, {"$inc": {"votes": 1}})
                data_base.needs.update_one({"_id": ObjectId(args["need_2"])}, {"$inc": {"votes": 1}})
                data_base.needs.update_one({"_id": ObjectId(args["need_3"])}, {"$inc": {"votes": 1}})
                data_base.needs.update_one({"_id": ObjectId(args["need_4"])}, {"$inc": {"votes": 1}})
                
                #creating array of the needs selected
                needs_list= [
                    data_base.needs.find_one({"_id": ObjectId(args["need_1"])}),
                    data_base.needs.find_one({"_id": ObjectId(args["need_2"])}),
                    data_base.needs.find_one({"_id": ObjectId(args["need_3"])}),
                    data_base.needs.find_one({"_id": ObjectId(args["need_4"])})
                ]

                #updating needs for user
                data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$set": {"needs": needs_list}})

            else:
                # updating votes on needs selected and those removed from users needs
                for i in range(4):
                    if len(user_01["needs"]) > i and user_01["needs"][i] is not None:
                        data_base.needs.update_one({"_id": user_01["needs"][i]["_id"]}, {"$inc": {"votes": -1}})
                        data_base.needs.update_one({"_id": ObjectId(args[f"need_{i+1}"])}, {"$inc": {"votes": 1}})

                new_needs_list = [
                    data_base.needs.find_one({"_id": ObjectId(args["need_1"])}),
                    data_base.needs.find_one({"_id": ObjectId(args["need_2"])}),
                    data_base.needs.find_one({"_id": ObjectId(args["need_3"])}),
                    data_base.needs.find_one({"_id": ObjectId(args["need_4"])})
                ]
                
                #updating needs for user
                data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$set": {"needs": new_needs_list}})

            user_updated = data_base.users.find_one({"_id": ObjectId(args["user_id"])})
            for item in user_updated["needs"]:
                item["_id"] = str(item["_id"])
            
            return {
                "user_needs": user_updated["needs"]
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

# parser for submitting a solution
solution_submit_parser = reqparse.RequestParser()
solution_submit_parser.add_argument("solution_01", location="form", type=str)
solution_submit_parser.add_argument("quality_01", location="form", type=str)
solution_submit_parser.add_argument("phone_number_01", location="form", type=str)
solution_submit_parser.add_argument("location_01", location="form", type=str)
solution_submit_parser.add_argument("details_01", location="form", type=str)
solution_submit_parser.add_argument("user_id", location="args", type=str)
solution_submit_parser.add_argument("need_id", location="args", type=str)

#parser for getting solution info
solution_info_parser = reqparse.RequestParser()
solution_info_parser.add_argument("user_id", location="args", type=str)
solution_info_parser.add_argument("solution_id", location="args", type=str)

#editing solution parser
edit_solution_parser = reqparse.RequestParser()
edit_solution_parser.add_argument("user_id", location="args", type=str)
edit_solution_parser.add_argument("solution_id", location="args", type=str)
edit_solution_parser.add_argument("solution_01", location="form", type=str)
edit_solution_parser.add_argument("quality_01", location="form", type=str)
edit_solution_parser.add_argument("phone_number_01", location="form", type=str)
edit_solution_parser.add_argument("location_01", location="form", type=str)
edit_solution_parser.add_argument("details_01", location="form", type=str)

class Solutions(Resource):
    # @jwt_required()
    def post(self):
        try:
            args = solution_submit_parser.parse_args()
            if data_base.solutions.find_one({"user_id": args["user_id"], "need_id": args["need_id"]}):
                return {
                    "status": False,
                    "message": "You Already Submitted a Solution for this Community Need :)"
                }
            else:
                solution_info = {
                    "business_name": args["solution_01"],
                    "quality": args["quality_01"],
                    "phone_number": args["phone_number_01"],
                    "location": args["location_01"],
                    "details": args["details_01"],
                    "user_id": args["user_id"],
                    "need_id": args["need_id"],
                    "date_added": datetime.date.today().strftime("%A, %d/%b/%Y"),
                    "time_added": datetime.datetime.now().strftime("%H:%M hrs"),
                    "flags": [],
                    "reviews": []
                }
                
                data_base.solutions.insert_one(solution_info)
                data_base.needs.update_one({"_id": ObjectId(args["need_id"])}, {"$push": {"solutions_submitted": str(solution_info["_id"])}})
                solution_info["_id"] = str(solution_info["_id"])

                return {
                    "status": True,
                    "message": "solution submitted :)",
                    "Solution": solution_info
                }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }            

    
    #getting solution info
    def get(self):
        try:
            args = solution_info_parser.parse_args()
            solution_info = data_base.solutions.find_one({"_id": ObjectId(args["solution_id"])})
            solution_info["_id"] = str(solution_info["_id"])
            return {
                "status": True,
                "solution": solution_info
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }
    
    #edit solution info
    # @jwt_required()
    def patch(self):
        try:
            args = edit_solution_parser.parse_args()
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$set": {"business_name": args["solution_01"],
                                                                                            "quality": args["quality_01"],
                                                                                            "phone_number": args["phone_number_01"],
                                                                                            "location": args["location_01"],
                                                                                            "details": args["details_01"]}})
            return {
                "status": True,
                "message": "Solution Updated Successfully :)"
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }

# rating and flag parser 
rating_and_flag_parser = reqparse.RequestParser()
rating_and_flag_parser.add_argument("flag", location="form", type=str)
rating_and_flag_parser.add_argument("star_1", location="form", type=str)
rating_and_flag_parser.add_argument("star_2", location="form", type=str)
rating_and_flag_parser.add_argument("star_3", location="form", type=str)
rating_and_flag_parser.add_argument("star_4", location="form", type=str)
rating_and_flag_parser.add_argument("star_5", location="form", type=str)
rating_and_flag_parser.add_argument("user_id", location="args", type=str)
rating_and_flag_parser.add_argument("solution_id", location="args", type=str)

class SolutionReviews(Resource):
    # @jwt_required()
    def post(self):
        try:
            args = rating_and_flag_parser.parse_args()
            rating_array = [
                args["star_1"],
                args["star_2"],
                args["star_3"],
                args["star_4"],
                args["star_5"]
            ]
            solution_rating = 0
            for item in rating_array:
                if item == "True":
                    solution_rating += 1
            
            # for the reviews
            if data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "reviews": {"$elemMatch": {"user_id": args["user_id"]}}}) == None:
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"reviews": {
                    "user_id": args["user_id"],
                    "solution_rating": solution_rating
                }}})
            elif data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "reviews": {"$elemMatch": {"user_id": args["user_id"]}}}) != None:
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"reviews": {"user_id": args["user_id"]}}})
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"reviews": {
                    "user_id": args["user_id"],
                    "solution_rating": solution_rating
                }}})           

            # for the flags
            if args["flag"] == "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "flags": {"$in": [args["user_id"]]}}) == None:
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"flags": args["user_id"]}})
            elif args["flag"] == "False" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "flags": {"$in": [args["user_id"]]}}) != None:
                print("passed here")
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"flags": args["user_id"]}})

            return {
                "status": True,
                "message": "Your Review Has Been Submitted Successfully! :)"
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }