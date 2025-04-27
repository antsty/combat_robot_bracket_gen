import os.path
import sqlite3
import sys

import robot

"""
Database manager
"""

def create_db(filename, num_rounds):
    """
    Create a database with the supplied filename

    :param filename: string, name of the database file to create
    :param num_rounds: integer, number of rounds
    
    return sqlite3 Connection object, the database
    """
    
    if os.path.isfile(filename):
        print(f"ERROR: file {filename} already exists.")
        sys.exit(1)
    
    db = sqlite3.connect(filename)
    
    db.execute("CREATE TABLE Metadata (num_rounds)")
    db.execute(f"INSERT INTO Metadata (num_rounds) VALUES ({num_rounds})")
    
    robot_sql = "CREATE TABLE Robot (id, name, roboteer"
    for i in range(0, num_rounds):
        robot_sql += f", round_{i+1} DEFAULT 0"
    robot_sql += ")"
    
    db.execute(robot_sql)
    db.execute("CREATE TABLE Fight (id, round_id, l_robot_id, l_score, r_robot_id, r_score)")
    
    return db;

def open_db(filename):
    """
    Open a database with the supplied filename

    :param filename: string, name of the database file to be opened
    
    return sqlite3 Connection object, the database
    """
    
    if not os.path.isfile(filename):
        print(f"ERROR: file {filename} does not exist.")
        sys.exit(1)
    
    db = sqlite3.connect(filename)
    cur = db.cursor()
    
    return db
    
def close_db(db, save_data):
    """
    Open a database with the supplied filename

    :param filename: string, name of the database file to close
    :param save_data: boolean, True if data should be saved, False otherwise
    """
    
    if save_data:
        db.commit() 
    db.close()

def add_robots(db, entrants):
    robots_to_add = []
    for id, robot_obj in entrants.items():
        robots_to_add.append((id, robot_obj.get_name(), robot_obj.get_team_id()))
        
    db.executemany("INSERT INTO Robot (id, name, roboteer) VALUES (?, ?, ?)", robots_to_add)

def load_existing_data(db):
    """
    Load the Robots and Fights from the database

    :param db: sqlite3 Connection object, the database
    
    return dictionary from ID to Robot object
    return integer, next robot ID
    return integer, next fight ID
    """
    
    cur = db.cursor()
    entrants = {}
    
    # Load Robots
    num_rounds = int(cur.execute("SELECT num_rounds FROM Metadata").fetchone()[0])
    
    cur_score_sql = "("
    for i in range(1, num_rounds):
        cur_score_sql += f"round_{i}"
        if i < num_rounds-1:
            cur_score_sql += "+"
    cur_score_sql += ") AS score"
    
    for row in cur.execute(f"SELECT id, name, roboteer, {cur_score_sql} FROM Robot"):
        new_robot = robot.Robot(row[0], row[1], row[2])
        new_robot.set_score(row[3])
        entrants[int(row[0])] = new_robot
                    
    # Load fights
    for row in cur.execute("SELECT id, l_robot_id, r_robot_id FROM Fight"):
        l_robot_id = int(row[1])
        r_robot_id = int(row[2])
        
        l_robot = entrants[l_robot_id]
        l_robot.add_fight(r_robot_id)
        entrants[l_robot_id] = l_robot
        
        r_robot = entrants[r_robot_id]
        r_robot.add_fight(l_robot_id)
        entrants[r_robot_id] = r_robot
    
    max_robot_id = cur.execute("SELECT MAX(id) FROM Robot").fetchone()
    max_fight_id = cur.execute("SELECT MAX(id) FROM Fight").fetchone()
    
    next_robot_id = max_robot_id[0] + 1 if max_robot_id[0] is not None else 1
    next_fight_id = max_fight_id[0] + 1 if max_fight_id[0] is not None else 1
     
    return entrants, next_robot_id, next_fight_id;

def get_teammates(db, robot_id):
    team = []
    for row in db.execute(f"SELECT id FROM Robot WHERE roboteer = (SELECT roboteer FROM Robot WHERE id = {robot_id})"):
        team.append(row[0])
    return team
    
def add_fights(db, fights_to_add):
    db.executemany("INSERT INTO Fight (id, round_id, l_robot_id, r_robot_id) VALUES (?, ?, ?, ?)", fights_to_add)
    
def commit_result(db, id, left, right):
    cur = db.cursor()
    cur.execute(f"UPDATE Fight SET l_score = {left}, r_score = {right} WHERE id = {id}")
    round_id = cur.execute(f"SELECT round_id FROM Fight WHERE id = {id}").fetchone()
    cur.execute(f"UPDATE Robot SET round_{round_id[0]} = {left} WHERE id = (SELECT l_robot_id FROM Fight WHERE id = {id})")
    cur.execute(f"UPDATE Robot SET round_{round_id[0]} = {right} WHERE id = (SELECT r_robot_id FROM Fight WHERE id = {id})")
    