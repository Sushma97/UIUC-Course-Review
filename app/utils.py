import os, sqlalchemy
from click import edit


#Stores additional functions that are used in other files

#class which stores all the query strings
class Query:

    qStatTotQueries = """SELECT count(reviewID) from Review"""
    qStatTotCourse = """SELECT count(title) from Course"""
    qStatTotProf = """SELECT count(profID) from Professor"""
    qStatTotStudents = """SELECT count(UIN) from Student"""
    qStatTotDepartments = """SELECT count(deptName) from Department"""

    #Query for reviews for a particular courseID
    qCourse = """select s.firstName, s.lastName, r.firstName, r.lastName, r.reviewID, r.reviewerUIN, r.reviewStanding, r.courseTerm, r.profComments, 
        r.courseComments, r.reviewerGrade, r.difficulty, r.usefulness, r.avgHrs, r.maxHrs, r.profRating 
        from Student s join (select * from Review natural join Professor where courseID='{arg1}' {arg2}) r on s.UIN = r.reviewerUIN {arg3};"""

    #Query for average review info for each course in a department
    qDept = """select courseID, title, avg(difficulty) as avgDifficulty, avg(usefulness) as avgUsefulness, avg(avgHrs) as avgAvgHrs, avg(maxHrs) as avgMaxHrs from Review natural join Course where deptID='{arg1}' group by courseID;"""
    
    #Query for aggregate information about an entire department
    qDeptAgg = """select avg(difficulty) as avgDifficulty, avg(usefulness) as avgUsefulness, avg(avgHrs) as avgAvgHrs, avg(maxHrs) as avgMaxHrs from Review natural join Course where deptID='{arg1}' group by deptID;"""

    #Query for reviews for a particular professor
    qProf = """select courseID, title, s.firstName, s.lastName, r.reviewID, r.reviewerUIN, r.reviewStanding, r.courseTerm, r.profComments, 
        r.courseComments, r.reviewerGrade, r.difficulty, r.usefulness, r.avgHrs, r.maxHrs, r.profRating from Course natural join Review r join Student s on r.reviewerUIN = s.UIN where profID={arg1} {arg2} {arg3};"""

    #Query for reviews made by a particular student
    qStud = """select * from Review r natural join Professor join Course c on r.courseID = c.CourseID where reviewerUIN={arg1};"""


    qprofId = """select profID from Professor where deptID=(select deptID from Course where courseID = :courseID) and firstName = :firstName and lastName = :lastName"""

    qProfID = """select sectionProfID from Enrollment where studentUIN = %s and sectionCourseID = %s and sectionTerm = %s"""

    qreview = """insert into Review (reviewerUIN, courseID, profID, reviewStanding, courseTerm, profComments, courseComments, reviewerGrade, difficulty, usefulness, avgHrs, maxHrs, profRating) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

    #Update the database by deleting a review with a particular ID
    qDelete = """delete from Review where reviewID={arg1};"""

    #Advanced query 1: show top 10 departments based on the lowest number of hours spent on average each week
    qMostTimeConsumingDepts = """select deptName, avg(avgHrs) as avgHrs, avg(maxHrs) as maxHrs from Department natural join Course natural join Review group by deptName order by avgHrs;"""

    #Advanced query 2: show professors with the highest ratings
    qProfRating = """select firstName, lastName, deptName, avg(profRating) as avgRating from Review natural join Professor natural join Department group by profID having count(*) > 15 order by avgRating desc limit 10;"""

    #Old version of advanced query 2 which we probs won't use
    qReviewStanding = """select reviewStanding, count(*) as count from Review where profID in (select profID from Professor natural join Review where deptID='{arg1}' group by profID having profRating > avg(profRating)) group by reviewStanding;"""

    qGetReview = """select * from Review where reviewID = %s"""

    qUpdateReview = "Update Review set profComments = %s, courseComments = %s, reviewerGrade = %s, difficulty = %s , usefulness = %s, avgHrs = %s, maxHrs = %s, profRating = %s where reviewID=%s"

    qGetOffenses = "SELECT * FROM studentAvgOffensiveCount ORDER BY num_offensive DESC;"

    qGetOffendedProfs = "SELECT * FROM mostOffendedProfs ORDER BY num_offensive DESC;"

    qInsertBadWord = """insert into bad_words (word) values ('{arg1}');"""

    qGetBadWords = """SELECT * from bad_words"""

    qCallOffenseRecount = "call fetch_offenses3;"


    autcomplete = "(select c.courseID as names from Course c where lower(c.courseID) like {arg1} limit 3) union (select d.deptID as names from Department d where lower(d.deptID) like {arg1} limit 3) union (select p.firstName as names from Professor p where lower(p.firstName) like {arg1} limit 2) union (select p.lastName as names from Professor p where lower(p.lastName) like {arg1} limit 1);"


# from https://www.geeksforgeeks.org/edit-distance-dp-5/ 
# returns 'closeness' of two strings
def editDistance(str1, str2, m, n):
    """
    :param str str1: The person sending the message
    :param str str2: The recipient of the message
    :param int m: The body of the message
    :param int n: The priority of the message, can be a number 1-5
    :return: 'closeness'
    :rtype: int
    """

    # If first string is empty, the only option is to
    # insert all characters of second string into first
    if m == 0:
        return n

    # If second string is empty, the only option is to
    # remove all characters of first string
    if n == 0:
        return m

    # If last characters of two strings are same, nothing
    # much to do. Ignore last characters and get count for
    # remaining strings.
    if str1[m-1] == str2[n-1]:
        return editDistance(str1, str2, m-1, n-1)

    # If last characters are not same, consider all three
    # operations on last character of first string, recursively
    # compute minimum cost for all three operations and take
    # minimum of three values.
    return 1 + min(editDistance(str1, str2, m, n-1),    # Insert
                editDistance(str1, str2, m-1, n),    # Remove
                editDistance(str1, str2, m-1, n-1)    # Replace
                )
 
