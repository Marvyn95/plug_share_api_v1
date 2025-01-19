from flask_restful import Resource, reqparse
import bcrypt
from flask import jsonify
from plug_share import data_base, jwt
from bson import ObjectId
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime
import secrets

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
                "role": "Endorser",
                "stars": 0,
                "solutions_flagged": [],
                "solutions_endorsed": [],
                "handshakes": 0,
                "handshakes_given": []
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


    # getting user page info
    def get(self):
        try:
            args = existing_user_parser.parse_args()
            user_01 = data_base.users.find_one({"_id": ObjectId(args["user_id"])})
            user_01["_id"] = str(user_01["_id"])
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
                        "user_id": str(user_01["_id"]),
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

            # checking if new email already exists in database for another user 
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

# parser for adding/voting need to list
needs_selection_parser = reqparse.RequestParser()
needs_selection_parser.add_argument("sub_category_id", type = str, location = "form")
needs_selection_parser.add_argument("location", type = str, location = "form")
needs_selection_parser.add_argument("purpose", type = str, location = "form")
needs_selection_parser.add_argument("user_id", type = str, location = "args")

# parser for deleting need from user needs list
needs_deletion_parser = reqparse.RequestParser()
needs_deletion_parser.add_argument("user_id", type=str, location="args")
needs_deletion_parser.add_argument("sub_category_id", type=str, location="args")
needs_deletion_parser.add_argument("need_id", type=str, location="args")


class CommunityNeeds(Resource):
    # getting top needs 
    def get(self):
        #getting all need categories
        user_selected_needs = [item for item in list(data_base.needs.find()) if item["votes"] != []]
        #sorting based on largest selected category and getting top 30 categories
        sorted_user_selected_needs = sorted(user_selected_needs, key = lambda x: len(x["votes"]))
        needs_01 = []
        grouped_top_needs = []
        count = 0
        for item in sorted_user_selected_needs:
            for x in item["votes"]:
                user = data_base.users.find_one({"_id": ObjectId(x["user_id"])})
                for y in user["needs"]:
                    if y["need_id"] == x["need_id"]:
                        need = y
                        break

                need["need_category"] = item["categories"]
                need["need_sub_category"] = item["sub_categories"]
                need["poster's_id"] = x["user_id"]
                need["poster's_name"] = user["user_name"]
                need["poster's_email"] = user["email"]
                need["poster's_stars"] = user["stars"]
                need["poster's_handshakes"] = user["handshakes"]

                need["need_solutions"] = data_base.solutions.find({"need_id": x["needs"]})

                needs_01.append(need)
                count += 1
            
            grouped_top_needs.append({
                "subcategory": item["sub_categories"],
                "needs": needs_01
            })

            needs_01 = []

        return{
            "count": count,
            "top_needs": grouped_top_needs
        }

    # adding needs to profile
    # @jwt_required()
    def post(self):
        args = needs_selection_parser.parse_args()
        user_01 = data_base.users.find_one({"_id": ObjectId(args["user_id"])})

        if len(user_01["needs"]) < 3:
            #updating votes in need categories
            need_id = secrets.token_hex(16)
            data_base.needs.update_one({"_id": ObjectId(args["sub_category_id"])}, {"$push": {"votes": {
                "user_id": args["user_id"],
                "need_id": need_id
            }}})

            #updating user needs 
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"needs": {
                "need_id": need_id,
                "sub_category_id": args["sub_category_id"],
                "location": args["location"],
                "purpose": args["purpose"]
            }}})
            return {
                "status": True,
                "message": "needs updated successfully :)"
            }
        else:
            return {
                "status": False,
                "message": "needs already full :( !!)"
            }

    def delete(self):
        args = needs_deletion_parser.parse_args()
        # deleting need from user's need list
        data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"needs": {"need_id": args["need_id"]}}})
        #reducing votes in the general needs list
        votes = data_base.needs.find_one({"_id": ObjectId(args["sub_category_id"])})["votes"]
        if votes:
            try:
                votes = [vote for vote in votes if vote["need_id"] != args["need_id"]]
            except:
                pass
        data_base.needs.update_one({"_id": ObjectId(args["sub_category_id"])}, {"$set": {"votes": votes}})
        return {
            "status": True,
            "message": "Need deleted Successfully :)"
        }
    

# parser for submitting a solution
solution_submit_parser = reqparse.RequestParser()
solution_submit_parser = reqparse.RequestParser()
solution_submit_parser.add_argument("user_id", location="args", type=str)
solution_submit_parser.add_argument("need_id", location="args", type=str)
solution_submit_parser.add_argument("sub_category_id", location="args", type=str)
solution_submit_parser.add_argument("solution", location="form", type=str)
solution_submit_parser.add_argument("phone_number", location="form", type=str)
solution_submit_parser.add_argument("email", location="form", type=str)
solution_submit_parser.add_argument("location", location="form", type=str)
solution_submit_parser.add_argument("details", location="form", type=str)

#parser for getting solution info
solution_info_parser = reqparse.RequestParser()
solution_info_parser.add_argument("user_id", location="args", type=str)
solution_info_parser.add_argument("solution_id", location="args", type=str)

#editing solution parser
edit_solution_parser = reqparse.RequestParser()
edit_solution_parser.add_argument("user_id", location="args", type=str)
edit_solution_parser.add_argument("solution_id", location="args", type=str)
edit_solution_parser.add_argument("solution", location="form", type=str)
edit_solution_parser.add_argument("phone_number", location="form", type=str)
edit_solution_parser.add_argument("email", location="form", type=str)
edit_solution_parser.add_argument("location", location="form", type=str)
edit_solution_parser.add_argument("details", location="form", type=str)


#delete solution parser
delete_solution_parser = reqparse.RequestParser()
delete_solution_parser.add_argument("user_id", location="args", type=str)
delete_solution_parser.add_argument("solution_id", location="args", type=str)

class Solutions(Resource):
    # adding solution to specific need
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
                    "user_id": args["user_id"],
                    "need_id": args["need_id"],
                    "need_sub_category_id": args["sub_category_id"],
                    "business_name": args["solution"],
                    "phone_number": args["phone_number"],
                    "email": args["email"],
                    "location": args["location"],
                    "details": args["details"],
                    "date_added": datetime.date.today().strftime("%A, %d/%b/%Y"),
                    "time_added": datetime.datetime.now().strftime("%H:%M hrs"),
                    "flags": [],
                    "handshakes": [],
                    "endorsements": [],
                    "points": 0,
                    "alternative_solutions": [],
                    "primary_solutions": []
                }
                
                #populating database collections
                data_base.solutions.insert_one(solution_info)
                data_base.needs.update_one({"_id": ObjectId(args["sub_category_id"])}, {"$push": {"solutions_submitted": {
                    "solution_poster_id": args["user_id"],
                    "need_id": args["need_id"],
                    "solution_id": str(solution_info["_id"])
                }}})
                data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"solutions_submitted": str(solution_info["_id"])}})
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
        args = solution_info_parser.parse_args()
        solution_info = data_base.solutions.find_one({"_id": ObjectId(args["solution_id"])})
        solution_info["_id"] = str(solution_info["_id"])
        
        #getting poster's info and adding it to return odject
        poster_info = data_base.users.find_one({"_id": ObjectId(solution_info["user_id"])})
        solution_info["poster_info"] = {
            "poster_name": poster_info["user_name"],
            "poster_email": poster_info["email"],
            "poster_stars": poster_info["stars"],
            "poster_points": poster_info["points"]
        }

        #getting need info and adding it to return object
        category_info = data_base.needs.find_one({"_id": ObjectId(solution_info["need_sub_category_id"])})
        for x in category_info["votes"]:
            if x["need_id"] == solution_info["need_id"]:
                need_poster_info = data_base.users.find_one({"_id": ObjectId(x["user_id"])})
                for y in need_poster_info["needs"]:
                    if y["need_id"] == solution_info["need_id"]:
                        solution_info["need_info"] = { 
                            "category": category_info["categories"],
                            "sub_category": category_info["sub_categories"],
                            "location_needed": y["location"],
                            "purpose": y["purpose"]
                        }

        return {
            "status": True,
            "solution": solution_info
        }

    
    #edit solution info
    # @jwt_required()
    def patch(self):
        try:
            args = edit_solution_parser.parse_args()
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$set": {"business_name": args["solution"],
                                                                                            "phone_number": args["phone_number"],
                                                                                            "email": args["email"],
                                                                                            "location": args["location"],
                                                                                            "details": args["details"]}})
            return {
                "status": True,
                "message": "Solution Updated Successfully :)"
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
            }
        
    # delete solution
    # @jwt_required()
    def delete(self):
        try:
            args = delete_solution_parser.parse_args()

            #getting solution info before deletion
            solution_info = data_base.solutions.find_one({"_id": ObjectId(args["solution_id"])})

            #deleting solution from solutions collection
            data_base.solutions.delete_one({"_id": ObjectId(args["solution_id"])})

            #deleting solution references from needs collection as well
            data_base.needs.update_one({"_id": ObjectId(solution_info["need_sub_category_id"])}, {"$pull": {"solutions_submitted": {
                "solution_id": args["solution_id"]
            }}})

            #deleting solution references from users collection as well
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"solutions_submitted": args["solution_id"]}})

            #deleting solution references from all its alternatives references as well
            for item in solution_info["primary_solutions"]:
                data_base.solutions.update_one({"_id": ObjectId(item["primary_solution_id"])}, {"$pull": {"alternative_solutions": {
                    "alternative_solution_id": str(solution_info["_id"])
                }}})

            return {
                "status": True,
                "message": "Solution Has Been Deleted Successfully ! :)"
            }


        except Exception as e:
            return {
                "status": False,
                "message": "solution Does Not Exist Or Has Been Deleted!" 
            }


# review, endorsement and flag parser 
review_parser = reqparse.RequestParser()
review_parser.add_argument("user_id", location="args", type=str)
review_parser.add_argument("solution_id", location="args", type=str)
review_parser.add_argument("handshake", location="form", type=str)
review_parser.add_argument("endorsement", location="form", type=str)
review_parser.add_argument("flag", location="form", type=str)

class SolutionReviews(Resource):
    # @jwt_required()
    def post(self):
        args = review_parser.parse_args()
        #getting user and solution info from db
        user_info = data_base.users.find_one({"_id": ObjectId(args["user_id"])})
        solution_info = data_base.solutions.find_one({"_id": ObjectId(args["solution_id"])})
                
        #handshaking
        if args["handshake"] == "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "handshakes": {"$in": [args["user_id"]]}}) == None:
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"handshakes": args["user_id"]}})
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"handshakes_given": args["solution_id"]}})
            #updating handshakes for solution owner
            data_base.users.update_one({"_id": ObjectId(solution_info["user_id"])}, {"$inc": {"handshakes": 1}})
            
            #endorsers ?????

        #removing handshaking
        elif args["handshake"] != "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "handshakes": {"$in": [args["user_id"]]}}) != None:
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"handshakes": args["user_id"]}})
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"handshakes_given": args["solution_id"]}})
            #updating handshakes for solution owner
            data_base.users.update_one({"_id": ObjectId(solution_info["user_id"])}, {"$inc": {"handshakes": -1}})


        # flagging and updating flag status
        #flagging
        if args["flag"] == "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "flags.user_id": args["user_id"]}) == None:
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"flags": {
                "user_id": args["user_id"],
                "flag_enforcement_status": False 
            }}})
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"solutions_flagged": args["solution_id"]}})
        #removing flag
        elif args["flag"] != "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "flags.user_id": args["user_id"]}) != None:
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"flags": {"user_id": args["user_id"]}}})
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"solutions_flagged": args["solution_id"]}})


        # endorsing and updating endorsement status
        #endorsing
        #checking if user is an endorser
        if user_info["role"] == "Endorser":
            #endorsing solution
            if args["endorsement"] == "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "endorsements": {"$in": [args["user_id"]]}}) == None:           
                #checking if user has endorsed any other solution for the same specific need
                #getting all other solutions
                other_solutions_submitted = [sol for sol in data_base.solutions.find({"need_id": solution_info["need_id"]}) if str(sol["_id"]) != args["solution_id"]]
                # checking if user has endorsed any
                endorsement_status = False
                for item in list(other_solutions_submitted):
                    if args["user_id"] in item["endorsements"]:
                        endorsement_status = True
                if not endorsement_status:
                    #updating endorsement in solution information
                    data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"endorsements": args["user_id"]}})
                    #updating endorsement in users profile
                    data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"solutions_endorsed": args["solution_id"]}})
                    #increasing solution points based on endorser points
                    data_base.solution.update_one({"_id": ObjectId(args["solution_id"])}, {"$inc": {"points": user_info["handshakes"]}})

            #removing endorsement
            elif args["endorsement"] != "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "endorsements": {"$in": [args["user_id"]]}}) != None:
                #updating endorsement in solution information
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"endorsements": args["user_id"]}})
                #updating endorsement in users profile
                data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"solutions_endorsed": args["solution_id"]}})
                #decreasing solution points based on endorser points
                data_base.solution.update_one({"_id": ObjectId(args["solution_id"])}, {"$inc": {"points": -user_info["handshakes"]}})

        return {
            "status": True,
            "message": "Your Review Has Been Submitted Successfully! :)"
        }


#getting endorsed solutions parser
get_endorsements_parser = reqparse.RequestParser()
get_endorsements_parser.add_argument("user_id", location="args", type=str)

#submit alternative parser
submit_alternative_parser = reqparse.RequestParser()
submit_alternative_parser.add_argument("user_id", location="args", type=str)
submit_alternative_parser.add_argument("solution_id", location="args", type=str)
submit_alternative_parser.add_argument("alternative_id", location="args", type=str)

#delete alternative parser
delete_alternative_parser = reqparse.RequestParser()
delete_alternative_parser.add_argument("user_id", location="args", type=str)
delete_alternative_parser.add_argument("solution_id", location="args", type=str)
delete_alternative_parser.add_argument("alternative_id", location="args", type=str)


#getting user endorsed solutions
class Endorsements(Resource):
    #get all solutions endorsed by user
    def get(set):
        args = get_endorsements_parser.parse_args()
        endorsements_list = data_base.users.find_one({"_id": ObjectId(args["user_id"])})["solutions_endorsed"]
        detailed_endorsements_list = []
        #generating endorsement objects
        for item in endorsements_list:
            endorsement = data_base.solutions.find_one({"_id": ObjectId(item)})
            endorsement["_id"] = str(endorsement["_id"])
            detailed_endorsements_list.append(endorsement)
        
        return {
            "status": True,
            "endorsements": detailed_endorsements_list
        }
    
    #submitting alternative
    def post(self):
        args = submit_alternative_parser.parse_args()

        if not data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "alternative_solutions": {"$elemMatch": {
            "submitter_id": args["user_id"], "alternative_solution_id": args["alternative_id"]
        }}}):
            #adding alternative solution to the primary
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"alternative_solutions": {
                "submitter_id": args["user_id"],
                "alternative_solution_id": args["alternative_id"]
            }}})
            #adding primary solution to alternative
            data_base.solutions.update_one({"_id": ObjectId(args["alternative_id"])}, {"$push": {"primary_solutions": {
                "submitter_id": args["user_id"],
                "primary_solution_id": args["solution_id"]            
            }}})

            return {
                "status": True,
                "message": "Your Alternative Has Been Submitted Successfully! :)"
            }
        else:
            return {
                "status": False
            }

    #remove alternative
    def delete(self):
        args = delete_alternative_parser.parse_args()
        if data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "alternative_solutions": {"$elemMatch": {
            "submitter_id": args["user_id"], "alternative_solution_id": args["alternative_id"]
        }}}):
            #removing alternative solution from primary
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"alternative_solutions": {
                "submitter_id": args["user_id"],
                "alternative_solution_id": args["alternative_id"]
            }}})
            #removing primary solution from alternative
            data_base.solutions.update_one({"_id": ObjectId(args["alternative_id"])}, {"$pull": {"primary_solutions": {
                "submitter_id": args["user_id"],
                "primary_solution_id": args["solution_id"]            
            }}})

            return {
                "status": True,
                "message": "Your Alternative Has Been Removed  Successfully! :)"
            }
        else:
            return {
                "status": False
            }