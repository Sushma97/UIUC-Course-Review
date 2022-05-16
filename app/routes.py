from contextlib import nullcontext
from crypt import methods
from typing import OrderedDict
from app import app
from app import database as db_helper
from flask import redirect, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from app import db, queries
from app import utils as u


#These store the keys returned by the filter form to narrow search results
courseFilters = ["firstName","lastName","courseTerm","reviewStanding","reviewerGrade"]
courseOrderBys = ["difficulty","usefulness","avgHrs","maxHrs","profRating"]
profFilters = ["courseID","courseTerm","reviewStanding","reviewerGrade"]
profOrderBys = ["difficulty","usefulness","avgHrs","maxHrs","profRating","courseIDob"]

"""
Home page route
- GET request loads the main page with some general information about different departments and professors
"""
@app.route("/", methods=["GET"])
def homepage():
    
    #Run advanced query 1 
    conn = db.connect()
    deptsByAvgHrs = conn.execute(queries.qMostTimeConsumingDepts).fetchall()
    leastTimeConsumingDepts = deptsByAvgHrs[:5]
    mostTimeConsumingDepts = deptsByAvgHrs[-5:]
    mostTimeConsumingDepts.reverse()

    #Run advanced query 2
    topProfRatings = conn.execute(queries.qProfRating).fetchall()

    #Get general db info to display
    dbData = []
    dbData.append(["Reviews", conn.execute(queries.qStatTotQueries).all()[0][0]])
    dbData.append(["Courses", conn.execute(queries.qStatTotCourse).all()[0][0]])
    dbData.append(["Professors", conn.execute(queries.qStatTotProf).all()[0][0]])
    dbData.append(["Students", conn.execute(queries.qStatTotStudents).all()[0][0]])
    dbData.append(["Departments", conn.execute(queries.qStatTotDepartments).all()[0][0]])
    conn.close()

    return render_template("index.html", dbData = dbData, mCon=mostTimeConsumingDepts, lCon = leastTimeConsumingDepts, topProfs=topProfRatings) 


@app.route("/autocomplete/<inp>", methods=["GET"])
def autocomplete(inp):
    conn = db.connect()
    input_argument = "%%"+ inp.lower()+"%%"
    query = queries.autcomplete.format(arg1="\'"+input_argument+"\'")
    #print(query)
    names_list = conn.execute(query).all()
    # filtered_dict = ["test","sushma","savitha"]
    resultList =[r[0] for r in names_list]
    #print(resultList)
    return make_response({"listaing":resultList}, 200)


"""
Route for submitting a search form on any page
 - POST request parses whatever the user entered into the search form
"""
@app.route("/search", methods=["POST"])
def search():
    #Extract search info
    search = request.form["search"]
    
    #Search db for entries
    #First check courses 
    conn = db.connect()
    queryRes = conn.execute(f"select courseID from Course where courseID='{search}';").fetchall()

    if len(queryRes) == 1:
        #We found the entry, show the reviews for this course
        conn.close()
        return redirect(url_for("showCourse",courseID=search.upper()))
    
    #If no result check department
    else:
        query = f"select deptID, deptName from Department where deptID='{search}';"
        queryRes = conn.execute(query).fetchone()
        if queryRes:
            
            #We found the entry, show the reviews for this department
            conn.close()
            return redirect(url_for("showDepartment",deptID=queryRes[0],deptName=queryRes[1]))
        
        #if no result check profs
        else:
            
            names = search.split(" ")
            firstName = names[0]
            query = f"select profID, firstName, lastName from Professor where firstName like '{firstName}'"
            if len(names) > 1:
                lastName = names[1]
                query += f" and lastName like '{lastName}%%'" #Note need to add %% (equivalent to % in sql) at the end for debugging purposes
            query += ";"
            queryRes = conn.execute(query).fetchone()
            if queryRes:
                #We found the entry, show the reviews for this professor
                conn.close()
                profID, firstName, lastName = queryRes
                return redirect(url_for("showProfessor",profID=profID,firstName=firstName,lastName=lastName))
    
    conn.close()
    return render_template("error.html")


"""
Route for displaying a course's reviews
 - GET request renders the course page for the specified course
"""
@app.route("/course/<courseID>", methods=["GET","POST"])
def showCourse(courseID):
    conn = db.connect()
    if request.method == "GET":
        #Return all reviews without any filters
        reviews = conn.execute(queries.qCourse.format(arg1=courseID,arg2="",arg3="")).all()
    else:
        #Extract filters and order info from form
        attributes = [(key, request.form[key]) for key in courseFilters if request.form[key] != ""]
        orderBys = [key for key in courseOrderBys if key in request.form]

        whereClause = ""
        for t in attributes:
            whereClause += f"and {t[0]}='{t[1]}'"
        
        if len(orderBys) == 0:
            orderByClause = ""
        else:
            orderByClause = "order by "
            for k in orderBys:
                orderByClause += f"{k} DESC, "
            orderByClause = orderByClause[:-2]
        
        print(orderByClause)
        
        reviews = conn.execute(queries.qCourse.format(arg1=courseID,arg2=whereClause,arg3=orderByClause)).all()
        

    conn.close()
    return render_template("course.html",cID=courseID, rvs=reviews) 


"""
Route for displaying a department's courses 
 - GET request renders the department page for the specified department
"""
@app.route("/department/<deptID>_<deptName>")
def showDepartment(deptID,deptName):
    conn = db.connect()
    print(f"deptID is {deptID}")
    courseInfo = conn.execute(queries.qDept.format(arg1=deptID)).fetchall()
    aggregateInfo = conn.execute(queries.qDeptAgg.format(arg1=deptID)).fetchone()
    
    conn.close()
    return render_template("department.html",deptName=deptName, rvs=courseInfo, aggInfo=aggregateInfo)
    

"""
Route for displaying a professor's reviews
 - GET request renders the professor page for the specified professor
"""
@app.route("/professor/<profID>_<firstName>_<lastName>", methods=["GET","POST"])
def showProfessor(profID,firstName,lastName):
    conn = db.connect()
    if request.method == "GET":
        reviews = conn.execute(queries.qProf.format(arg1=profID,arg2="",arg3="")).fetchall() 
    else:
        print("\n\nFILTERING REVIEWS\n\n")
        #Extract filters and order info from form
        attributes = [(key, request.form[key]) for key in profFilters if request.form[key] != ""]
        orderBys = [key for key in profOrderBys if key in request.form]

        whereClause = ""
        for t in attributes:
            whereClause += f"and {t[0]}='{t[1]}'"
        
        if len(orderBys) == 0:
            orderByClause = ""
        else:
            orderByClause = "order by "
            for k in orderBys:
                if k == 'courseIDob':
                    k = 'courseID'
                orderByClause += f"{k} DESC, "
            orderByClause = orderByClause[:-2]

        print(orderByClause)
        
        reviews = conn.execute(queries.qProf.format(arg1=profID,arg2=whereClause,arg3=orderByClause)).fetchall() 

    conn.close()
    profInfo = {"firstName": firstName, "lastName": lastName, "profID": profID}
    return render_template("professor.html",profInfo=profInfo, rvs=reviews) 




"""
Route for the login page
 - GET request just loads the login form
 - POST request parses login form and redirects user back to login form (if invalid credentials) or to their student page (if valid credentials)
"""
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if 'user' in session:
            flash(f"Already logged in as {session['user'][1]}")
            return redirect(url_for("showStudent",UIN=session['user'][0]))
        else: 
            return render_template("login.html")
    else:
        UIN = request.form["UIN"]
        pw = request.form["pw"]

        #Verify pw
        query = f"select password, firstName from Student where UIN={UIN};"
        successfulLogin = False
        conn = db.connect()
        try:
            queryRes = conn.execute(query).fetchone()
            if len(queryRes) != 0:
                expectedPw, firstName = queryRes
                if pw == expectedPw:
                    #successful login 
                    session["user"] = (UIN, firstName) #ERROR WITH SESSION, NEED TO SET SECRET KEY
                    successfulLogin = True

        except:
            #Unsuccessful login, query caused an error
            pass
            
        conn.close()
        if successfulLogin:
            flash("Sucessfully logged in!")
            return redirect(url_for("showStudent",UIN=UIN)) #load student reviews if login successful
        else:
            flash("Incorrect UIN or password")
            return render_template("login.html") #otherwise just keep login page open



"""
Route for the logout page
- GET request removes the current user from the session and redirects them back to the login page
"""
@app.route("/logout")
def logout():
    if "user" in session:
        flash("Successfully logged out","info") #second arg is a default category which automatically styles the message
    session.pop("user",None)
    return redirect(url_for("login"))



"""
Route for adding a new review
 - GET request renders the form for the user to submit (user must be logged in)
 - POST request parses the review form by adding entry to the database and redirects user to their student page
"""
@app.route("/review", methods=["GET", "POST"])
def newReviewPage():
    if request.method == "GET":
        print("session is {}".format(session))
        if 'user' in session:
            return render_template("review.html")
        else:
            flash("Please log in")
            return redirect(url_for("login"))
    else:
        courseid = request.form["courseid"]
        reviewStanding = request.form["reviewStanding"]
        courseTerm = request.form["CourseTerm"] + request.form["Year"]
        grade = request.form["grade"]

        try:
            difficulty = request.form["stard"]
        except:
            difficulty = "0"
        
        try:
            usefulness = request.form["staru"]
        except:
            usefulness = "0"
        
        try:
            profRating = request.form["starp"]
        except:
            profRating = "0"
        
        avgHours = request.form["avgHours"].strip()
        if not avgHours:
            avgHours = None
        maxHours = request.form["maxHours"].strip()
        if not maxHours:
            maxHours = None

        profComments = request.form["profComments"]
        courseComments = request.form["courseComments"]
        reviewerUIN = session['user'][0]


        conn = db.connect()
        try:

            profIdQuery = (reviewerUIN, courseid, courseTerm)
            profId = conn.execute(u.Query.qProfID, profIdQuery).fetchone()
            if not profId:
                flash(u'Please check the input fields. Provide review only for the course you are enrolled in.', 'error')
                return redirect(url_for("newReviewPage"))
            insertTuple = (reviewerUIN, courseid, profId[0], reviewStanding, courseTerm, profComments, courseComments, grade, difficulty, usefulness, avgHours, maxHours, profRating)
            result = conn.execute(u.Query.qreview, insertTuple)
            if not result:
    
                flash(u'Please check the input fields.', 'error')
                return redirect(url_for("newReviewPage"))
        except Exception as e:
            #Unsuccessful login, query caused an error
            print(e)
            if "Cannot insert review, student is banned" in str(e):
                flash(u'You cannot insert a review, too many offenses', 'error')
            else:
                flash(u'Please check the input fields', 'error')
            return redirect(url_for("newReviewPage"))
        conn.close()
        return redirect(url_for("showStudent",UIN=session['user'][0]))


"""
Route for editing an existing review
"""
@app.route("/review/<reviewID>", methods=["GET", "POST"])
def editReview(reviewID):
    if 'user' in session:
        #Verify that this user is the author of this review (query DB for this review)
        #If so, load page for user to edit review
        conn = db.connect()
        try:
            # existingReview = conn.execute(queries.qGetReview, (reviewID)).fetchone()
            grade = request.form["grade"]
            difficulty = request.form["difficulty"]
            usefulness = request.form["usefulness"]
            profRating = request.form["profRating"]
            avgHours = request.form["avgHours"].strip()
            if not avgHours:
                avgHours = None
            maxHours = request.form["maxHours"].strip()
            if not maxHours:
                maxHours = None
            profComments = request.form["profComments"]
            courseComments = request.form["courseComments"]
            updateTuple = (profComments, courseComments, grade, difficulty, usefulness, avgHours, maxHours, profRating, reviewID)
            result = conn.execute(u.Query.qUpdateReview, updateTuple)
            conn.close()
            return redirect(url_for("showStudent",UIN=session['user'][0]))
        except:
            flash(u'Please check the input fields', 'error')
            return redirect(url_for("showStudent",UIN=session['user'][0]))

    else:
        return redirect(url_for("login"))

"""
Route for deleting an existing review
"""
@app.route("/delete/<reviewID>")
def deleteReview(reviewID):
    if 'user' in session:
        #Verify that this user is the author of this review (query DB for this review)
        #If so, delete review
        conn = db.connect()
        try:
            conn.execute(queries.qDelete.format(arg1=reviewID)) 
        except:
            pass
        conn.close()

        #Redirect user back to their page
        return redirect(url_for("showStudent",UIN=session['user'][0]))
    else:
        return redirect(url_for("login"))




"""
Route to display the user's existing reviews where they view, edit, and delete them
 - GET request shows renders the user's reviews (user must be logged in)
"""
@app.route("/student/<UIN>", methods=["GET"])
def showStudent(UIN):
    #If there is already a user logged in, render their student page with their existing reviews
    if "user" in session:
        
        #If the search UIN does not match the logged in UIN, redirect to the logged in UIN's page
        if session["user"][0] != UIN:
            return redirect(url_for("showStudent",UIN=session['user'][0]))

        conn = db.connect()
        reviews = conn.execute(queries.qStud.format(arg1=session['user'][0])).fetchall()
        conn.close()
        return render_template("student.html",firstName=session["user"][1],rvs=reviews)

    #If no user logged in, direct them to login page
    else:
        flash("Please log in")
        return redirect(url_for("login"))
        

@app.route("/19iSvnfeocgVoyjjYYR8MGJwBteHU-RJRGsw5kRi1xuk", methods=["GET","POST"])
def admin():

    conn = db.connect()
    if request.method == "POST":
        #If new word was submitted, add it to the bad_words table
        if request.form["submitBtn"] == "Submit":
            newBadWord = request.form["bad_word"] 
            if newBadWord:
                bad_words_ls = conn.execute(queries.qGetBadWords).fetchall()
                if newBadWord not in [''.join(i) for i in bad_words_ls]:
                    conn.execute(queries.qInsertBadWord.format(arg1=newBadWord))
    
        else:
            #Rerun SP if the refresh button is pressed
            conn.execute(queries.qCallOffenseRecount)
    
    
    #Extract the offenses
    offenses = conn.execute(queries.qGetOffenses).fetchall()
    mostOffendedProfs = conn.execute(queries.qGetOffendedProfs).fetchall()
    conn.close()
    
    return render_template("admin.html", otb=offenses, mostOffendedProfs=mostOffendedProfs)

    