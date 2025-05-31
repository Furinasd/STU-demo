/*
 Navicat Premium Dump SQL

 Source Server         : 114
 Source Server Type    : MySQL
 Source Server Version : 80040 (8.0.40)
 Source Host           : localhost:3306
 Source Schema         : stu

 Target Server Type    : MySQL
 Target Server Version : 80040 (8.0.40)
 File Encoding         : 65001

 Date: 31/05/2025 22:07:18
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version`  (
  `version_num` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`version_num`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for course
-- ----------------------------
DROP TABLE IF EXISTS `course`;
CREATE TABLE `course`  (
  `Cno` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Cname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Cpno` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Ccredit` smallint NULL DEFAULT NULL,
  `Tno` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`Cno`) USING BTREE,
  INDEX `Cpno`(`Cpno` ASC) USING BTREE,
  INDEX `Tno`(`Tno` ASC) USING BTREE,
  CONSTRAINT `course_ibfk_1` FOREIGN KEY (`Cpno`) REFERENCES `course` (`Cno`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `course_ibfk_2` FOREIGN KEY (`Tno`) REFERENCES `t` (`Tno`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `course_chk_1` CHECK (`Ccredit` > 0)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for sc
-- ----------------------------
DROP TABLE IF EXISTS `sc`;
CREATE TABLE `sc`  (
  `Sno` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Cno` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Grade` smallint NULL DEFAULT NULL,
  PRIMARY KEY (`Sno`, `Cno`) USING BTREE,
  INDEX `Cno`(`Cno` ASC) USING BTREE,
  CONSTRAINT `sc_ibfk_1` FOREIGN KEY (`Sno`) REFERENCES `student` (`Sno`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `sc_ibfk_2` FOREIGN KEY (`Cno`) REFERENCES `course` (`Cno`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `sc_chk_1` CHECK (`Grade` between 0 and 100)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for schedule
-- ----------------------------
DROP TABLE IF EXISTS `schedule`;
CREATE TABLE `schedule`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `cno` varchar(6) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `tno` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `classroom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `day_of_week` tinyint NOT NULL COMMENT '1-7表示周一到周日',
  `time_slot` tinyint NOT NULL COMMENT '1-12表示第1-12节课',
  `duration` tinyint NULL DEFAULT 2 COMMENT '课程持续节数，默认2节',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_teacher_time`(`tno` ASC, `day_of_week` ASC, `time_slot` ASC) USING BTREE,
  INDEX `idx_classroom_time`(`classroom` ASC, `day_of_week` ASC, `time_slot` ASC) USING BTREE,
  INDEX `idx_course_time`(`cno` ASC, `day_of_week` ASC, `time_slot` ASC) USING BTREE,
  CONSTRAINT `schedule_ibfk_1` FOREIGN KEY (`cno`) REFERENCES `course` (`Cno`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `schedule_ibfk_2` FOREIGN KEY (`tno`) REFERENCES `t` (`Tno`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for student
-- ----------------------------
DROP TABLE IF EXISTS `student`;
CREATE TABLE `student`  (
  `Sno` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Sname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `SID` char(18) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Sage` smallint NULL DEFAULT NULL,
  `Ssex` char(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Sdept` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`Sno`) USING BTREE,
  UNIQUE INDEX `SID`(`SID` ASC) USING BTREE,
  CONSTRAINT `student_chk_1` CHECK (`Sage` between 15 and 45),
  CONSTRAINT `student_chk_2` CHECK (`Ssex` in (_utf8mb4'男',_utf8mb4'女'))
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for t
-- ----------------------------
DROP TABLE IF EXISTS `t`;
CREATE TABLE `t`  (
  `Tno` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Tname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `Title` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`Tno`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for teaching
-- ----------------------------
DROP TABLE IF EXISTS `teaching`;
CREATE TABLE `teaching`  (
  `tno` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `cno` varchar(6) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`tno`, `cno`) USING BTREE,
  INDEX `cno`(`cno` ASC) USING BTREE,
  CONSTRAINT `teaching_ibfk_1` FOREIGN KEY (`cno`) REFERENCES `course` (`Cno`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `teaching_ibfk_2` FOREIGN KEY (`tno`) REFERENCES `t` (`Tno`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Procedure structure for calculate_avg_grade
-- ----------------------------
DROP PROCEDURE IF EXISTS `calculate_avg_grade`;
delimiter ;;
CREATE PROCEDURE `calculate_avg_grade`(IN stu_no CHAR(7), OUT avg_grade DECIMAL(5,2))
BEGIN
    SELECT AVG(Grade) INTO avg_grade
    FROM SC
    WHERE Sno = stu_no;
END
;;
delimiter ;

-- ----------------------------
-- Function structure for fn_avg_age_by_gender
-- ----------------------------
DROP FUNCTION IF EXISTS `fn_avg_age_by_gender`;
delimiter ;;
CREATE FUNCTION `fn_avg_age_by_gender`(gender CHAR(2))
 RETURNS decimal(5,2)
  DETERMINISTIC
BEGIN
    DECLARE result DECIMAL(5,2);
    SELECT AVG(Sage) INTO result
    FROM Student
    WHERE Ssex = gender;
    RETURN IFNULL(result, 0);
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for get_course_avg
-- ----------------------------
DROP PROCEDURE IF EXISTS `get_course_avg`;
delimiter ;;
CREATE PROCEDURE `get_course_avg`(IN course_name VARCHAR(20), OUT avg_score DECIMAL(5,2))
BEGIN
    SELECT AVG(sc.Grade) INTO avg_score
    FROM SC sc
    JOIN Course c ON sc.Cno = c.Cno
    WHERE c.Cname = course_name;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for p_Insertstu
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_Insertstu`;
delimiter ;;
CREATE PROCEDURE `p_Insertstu`(IN p_sno CHAR(7),
    IN p_sname VARCHAR(20),
    IN p_ssex CHAR(2),
    IN p_sage SMALLINT,
    IN p_sdept VARCHAR(20),
    OUT result_msg VARCHAR(100))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET result_msg = '插入失败：学号已存在或其他错误';
        ROLLBACK;
    END;
    
    START TRANSACTION;
    INSERT INTO Student(Sno, Sname, Ssex, Sage, Sdept)
    VALUES (p_sno, p_sname, p_ssex, p_sage, p_sdept);
    SET result_msg = '学生信息插入成功';
    COMMIT;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_course_avg_grade
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_course_avg_grade`;
delimiter ;;
CREATE PROCEDURE `sp_course_avg_grade`(IN course_name VARCHAR(20),
    OUT avg_score DECIMAL(5,2))
BEGIN
    SELECT AVG(sc.Grade) INTO avg_score
    FROM SC sc
    JOIN Course c ON sc.Cno = c.Cno
    WHERE c.Cname = course_name;
    
    SET avg_score = IFNULL(avg_score, 0);
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_student_avg_grade
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_student_avg_grade`;
delimiter ;;
CREATE PROCEDURE `sp_student_avg_grade`(IN stu_no CHAR(15),
    OUT avg_result DECIMAL(5,2))
BEGIN
    SELECT AVG(Grade) INTO avg_result
    FROM SC
    WHERE Sno = stu_no;
    
    SET avg_result = IFNULL(avg_result, 0);
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
