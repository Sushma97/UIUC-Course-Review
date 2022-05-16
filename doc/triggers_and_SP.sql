-- Trigger before update on Review table 
CREATE DEFINER=`root`@`%` TRIGGER `Review_BEFORE_UPDATE` BEFORE UPDATE ON `Review` FOR EACH ROW BEGIN
	IF EXISTS (SELECT * FROM bad_words b WHERE new.courseComments LIKE CONCAT('%', b.word, '%')) THEN
		SET new.courseComments = "Course Comment Omitted, Use of bad_words";
	END IF;
	IF EXISTS (SELECT * FROM bad_words b WHERE new.profComments LIKE CONCAT('%', b.word, '%')) THEN
        SET new.profComments = "Professor Comment Omitted, Use of bad_words";
	END IF;
END


-- Trigger before insert into Review table 
CREATE DEFINER=`root`@`%` TRIGGER `Review_BEFORE_INSERT` BEFORE INSERT ON `Review` FOR EACH ROW BEGIN
	DECLARE studentBanned BOOLEAN; 
    SELECT banned INTO studentBanned FROM Student WHERE Student.UIN = new.reviewerUIN;
    IF NOT studentBanned THEN
		IF EXISTS (SELECT * FROM bad_words b WHERE new.courseComments LIKE CONCAT('%', b.word, '%')) THEN
			SET new.courseComments = "Course Comment Omitted, Use of bad_words";
		END IF;
		IF EXISTS (SELECT * FROM bad_words b WHERE new.profComments LIKE CONCAT('%', b.word, '%')) THEN
			SET new.profComments = "Professor Comment Omitted, Use of bad_words";
		END IF;
	ELSE 
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Cannot insert review, student is banned";
	END IF;
END



-- Trigger for bad_words table 
CREATE DEFINER=`root`@`%` TRIGGER `bad_words_AFTER_INSERT` AFTER INSERT ON `bad_words` FOR EACH ROW BEGIN
	UPDATE Review r SET r.courseComments = "Course Comment Omitted, Use of bad_words" WHERE r.courseComments LIKE CONCAT('%', new.word, '%');
    UPDATE Review r SET r.profComments = "Professor Comment Omitted, Use of bad_words" WHERE r.profComments LIKE CONCAT('%', new.word, '%');
END



-- Stored procedure code: 
CREATE DEFINER=`root`@`%` PROCEDURE `fetch_offenses3`()
BEGIN
DECLARE done int default 0;
DECLARE num_offenses int default 0;
DECLARE num_reviews int default 0;
DECLARE curr_student_UIN INT;
DECLARE first_name VARCHAR(255);
DECLARE last_name VARCHAR(255);
DECLARE reviewCur CURSOR FOR SELECT UIN FROM Student;
DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

DROP TABLE IF EXISTS studentAvgOffensiveCount;

CREATE TABLE studentAvgOffensiveCount (
	student_UIN INT,
    firstName VARCHAR(255),
    lastName VARCHAR(255),
    num_offensive INT,
    num_classes_reviewed INT
);

DROP TABLE IF EXISTS mostOffendedProfs;

CREATE TABLE mostOffendedProfs (
	profID INT,
    firstName VARCHAR(255),
    lastName VARCHAR(255),
    num_offensive INT
);

OPEN reviewCur;
REPEAT
	FETCH reviewCur INTO curr_student_UIN;
	
    -- Advanced query 1 
    SELECT COUNT(reviewerUIN), firstName, lastName INTO num_offenses,first_name,last_name FROM 
    (SELECT * FROM Review WHERE reviewerUIN = curr_student_UIN) as r
    join Student s on (s.UIN = r.ReviewerUIN)
    WHERE r.courseComments = "Course Comment Omitted, Use of bad_words" or r.profComments = "Professor Comment Omitted, Use of bad_words";
            
	
    -- insert entry if the number of offenses is not 0
    IF num_offenses != 0 THEN
 		SET num_reviews = (SELECT COUNT(reviewerUIN) FROM Review
 		WHERE reviewerUIN = curr_student_UIN);
         
 		INSERT INTO studentAvgOffensiveCount(student_UIN, firstName, lastName, num_classes_reviewed, num_offensive) values (curr_student_UIN, first_name, last_name, num_reviews, num_offenses);
        commit;
        
     END IF;
     
     -- determine if student should be banned or not
	IF num_offenses >= 3 THEN
		UPDATE Student SET banned = True WHERE UIN = curr_student_UIN;
	ELSE 
		UPDATE Student SET banned = False WHERE UIN = curr_student_UIN;
	END IF;
    

UNTIL done
END REPEAT;

close reviewCur;


-- Advanced query 2: get most offensive courses and professors and add them to table
INSERT INTO mostOffendedProfs 
(SELECT profID, firstName, lastName, count(*) FROM Review natural join Professor 
where profComments = "Professor Comment Omitted, Use of bad_words" 
GROUP BY profID);
commit;


END