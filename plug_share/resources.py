from flask_restful import Resource, Api, reqparse
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
                    "role": "Member",
                    "stars": 0,
                    "points": 0,
                    "solutions_flagged": [],
                    "solutions_reviewed": [],
                    "solutions_endorsed": [] 
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
        try:
            #getting all need categories
            user_selected_needs = [item for item in list(data_base.needs.find()) if item["votes"] != []]
            #sorting based on largest selected category and getting top 30 categories
            sorted_user_selected_needs = sorted(user_selected_needs, key = lambda x: len(x["votes"]))[:30]
            top_needs = []
            count = 0
            for item in sorted_user_selected_needs:
                for x in item["votes"]:
                    user = data_base.users.find_one({"_id": ObjectId(x["user_id"])})
                    need = [y for y in user["needs"] if y["need_id"] == x["need_id"]]
                    
                    need[0]["need_category"] = item["categories"]
                    need[0]["need_sub_category"] = item["sub_categories"]
                    need[0]["poster's_id"] = x["user_id"]
                    need[0]["poster's_name"] = user["user_name"]
                    need[0]["poster's_email"] = user["email"]
                    need[0]["poster's_stars"] = user["stars"]
                    need[0]["poster's_points"] = user["points"]

                    top_needs.append(need[0])
                    count += 1
            return{
                "count": count,
                "top_needs": top_needs
            }
        except Exception as e:
            return {
                "status": "Error",
                "Error": e
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
                    "reviews": [],
                    "points": 0,
                    "endorsements": [],
                    "alternative": []
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
                vote = x
                need_poster_info = data_base.users.find_one({"_id": ObjectId(vote["user_id"])})
                for y in need_poster_info["needs"]:
                    if y["need_id"] == solution_info["need_id"]:
                        need = y
        
        solution_info["need_info"] = { 
            "category": category_info["categories"],
            "sub_category": category_info["sub_categories"],
            "location_needed": need["location"],
            "purpose": need["purpose"]
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
            return {
                "status": True,
                "message": "Solution Has Been Deleted Successfully ! :)"
            }
        except Exception as e:
            return {
                "status": False,
                "message": "solution Does Not Exist Or Has Been Deleted!" 
            }


# rating and flag parser 
review_parser = reqparse.RequestParser()
review_parser.add_argument("user_id", location="args", type=str)
review_parser.add_argument("solution_id", location="args", type=str)
review_parser.add_argument("flag", location="form", type=str)
review_parser.add_argument("star_1", location="form", type=str)
review_parser.add_argument("star_2", location="form", type=str)
review_parser.add_argument("star_3", location="form", type=str)
review_parser.add_argument("star_4", location="form", type=str)
review_parser.add_argument("star_5", location="form", type=str)
review_parser.add_argument("endorsement", location="form", type=str)


class SolutionReviews(Resource):
    # @jwt_required()
    def post(self):
        args = review_parser.parse_args()
        user_info = data_base.users.find_one({"_id": ObjectId(args["user_id"])})
        solution_info = data_base.solutions.find_one({"_id": ObjectId(args["solution_id"])})
        
        review_array = [args["star_1"], args["star_2"], args["star_3"], args["star_4"], args["star_5"]]
        
        solution_rating = 0
        for item in review_array:
            if item == "True":
                solution_rating += 1

        # for the reviews (reviewing and updating of reviews)
        # if its the first time to review item (give stars)
        if data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "reviews": {"$elemMatch": {"user_id": args["user_id"]}}}) == None:
            #updating review for solution info in database
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"reviews": {
                "user_id": args["user_id"],
                "solution_rating": solution_rating
            }}})
            
            #updating review for user info in database
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"solutions_reviewed": {
                "solution_id": args["solution_id"],
                "review": review_array
            }}})

            #updating solution owner's stars
            data_base.users.update_one({"_id": ObjectId(solution_info["user_id"])}, {"$inc": {"stars": solution_rating}})

            #distributing stars among endorsers
            #computing total weight distribution among endorsers (weight)
            weight = 0
            no_of_endorsers = len(solution_info["endorsements"])
            for item in solution_info["endorsements"]:
                weight += no_of_endorsers
                no_of_endorsers -= 1

            # distributing points based on stars to each endorsers
            no_of_endorsers = len(solution_info["endorsements"])
            for item in solution_info["endorsements"]:
                points_to_add = (no_of_endorsers/weight)*solution_rating
                data_base.users.update_one({"_id": ObjectId(item)}, {"$inc": {"points": points_to_add}})
                no_of_endorsers -= 1

        #if user already reviewed item
        elif data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "reviews": {"$elemMatch": {"user_id": args["user_id"]}}}) != None:

            #removing points from endorsers for old review
            #computing total weight among endorsers
            weight = 0
            no_of_endorsers = len(solution_info["endorsements"])
            for item in solution_info["endorsements"]:
                weight += no_of_endorsers
                no_of_endorsers -= 1

            # distributing points deductions based on stars to each endorsers
            no_of_endorsers = len(solution_info["endorsements"])
            # getting old solution rating
            old_solution_rating = 0
            for i in user_info["solutions_reviewed"]:
                if i["solution_id"] == str(solution_info["_id"]):
                    for j in i["review"]:
                        if j == "True":
                            old_solution_rating += 1
            
            # deducting points for old rating from endorsers
            for item in solution_info["endorsements"]:
                points_to_deduct = (no_of_endorsers/weight)*old_solution_rating
                data_base.users.update_one({"_id": ObjectId(item)}, {"$inc": {"points": -points_to_deduct}})
                no_of_endorsers -= 1

            #distributing new points to endorsers
            # distributing points based on stars to each endorsers
            no_of_endorsers = len(solution_info["endorsements"])
            for item in solution_info["endorsements"]:
                points_to_add = (no_of_endorsers/weight)*solution_rating
                data_base.users.update_one({"_id": ObjectId(item)}, {"$inc": {"points": points_to_add}})
                no_of_endorsers -= 1

            #removing old review from solution in database
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"reviews": {"user_id": args["user_id"]}}})
            #adding new review to solution in database
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"reviews": {
                "user_id": args["user_id"],
                "solution_rating": solution_rating
            }}})


            #updating solution owners stars in database
            for rev in user_info["solutions_reviewed"]:
            # getting former review from user (reviewer's) info and computing rating difference
                if rev["solution_id"] ==  args["solution_id"]:
                    old_star_length = 0
                    for star in rev["review"]:
                        if star == "True":
                            old_star_length +=1
                    rating_diff = solution_rating - old_star_length
            data_base.users.update_one({"_id": ObjectId(solution_info["user_id"])}, {"$inc": {"stars": rating_diff}})

            #updating review in user (reviewer) profile in database
            #removing old review from user info in database
            data_base.users.update_one({"_id" : ObjectId(args["user_id"])}, {"$pull": {"solutions_reviewed": {"solution_id": args["solution_id"]}}})
            #adding new review to user info in database
            data_base.users.update_one({"_id" : ObjectId(args["user_id"])}, {"$push": {"solutions_reviewed": {
                "solution_id": args["solution_id"],
                "review": review_array
            }}})


        # flagging and updating flag status
        #flagging
        if args["flag"] == "True" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "flags": {"$in": [args["user_id"]]}}) == None:
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$push": {"flags": args["user_id"]}})
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$push": {"solutions_flagged": args["solution_id"]}})
        #removing flag
        elif args["flag"] == "False" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "flags": {"$in": [args["user_id"]]}}) != None:
            data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"flags": args["user_id"]}})
            data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"solutions_flagged": args["solution_id"]}})

        # endorsing and updating endorsement status
        #endorsing
        #checking if user is an endorser
        if user_info["role"] == "Endorser":
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
                    data_base.solution.update_one({"_id": ObjectId(args["solution_id"])}, {"$inc": {"points": user_info["points"]}})


            #removing endorsement
            elif args["endorsement"] == "False" and data_base.solutions.find_one({"_id": ObjectId(args["solution_id"]), "endorsements": {"$in": [args["user_id"]]}}) != None:
                #updating endorsement in solution information
                data_base.solutions.update_one({"_id": ObjectId(args["solution_id"])}, {"$pull": {"endorsements": args["user_id"]}})
                #updating endorsement in users profile
                data_base.users.update_one({"_id": ObjectId(args["user_id"])}, {"$pull": {"solutions_endorsed": args["solution_id"]}})
                #decreasing solution points based on endorser points
                data_base.solution.update_one({"_id": ObjectId(args["solution_id"])}, {"$inc": {"points": -user_info["points"]}})

        return {
            "status": True,
            "message": "Your Review Has Been Submitted Successfully! :)"
        }