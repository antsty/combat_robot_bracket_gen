import argparse
import csv
#import random
import sys 
#import sqlite3

import db_manager
import robot
import round_generator

# Global values
free_robot_id = 1
free_fight_id = 1
num_robots = 0
has_melees = False

parser = argparse.ArgumentParser(prog="Fight Night Generator",
                                 description="Read an input CSV and output a list of fight night rounds",
                                 epilog="")

def load_robots_from_csv(filename, allow_odd):
    """
    Read a CSV file, returning a dictionary from ID to Robot object

    :param filename: string CSV filename, with "Roboteer", "Robot" and "Tech Checked"
    :param allow_odd: boolean, if True allow odd number of entrants
    """
    next_robot_id = 1
    next_team_id = 1
    
    with open(filename, newline='') as csvfile:
        robots = {}
        teams = {}
        
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            name = row["Robot"].strip(' "')
            team_name = row["Roboteer"].strip()
            tech_checked = row["Tech Checked"].strip()
            
            if tech_checked.lower() == "y":                
                team_id = 0
                
                # If we have seen this team before, get its id
                if team_name in teams:
                    team_id = teams[team_name]
                else:
                    team_id = next_team_id
                    teams[team_name] = team_id
                    next_team_id += 1
                
                new_robot = robot.Robot(next_robot_id, name, team_id)
                
                robots[new_robot.id] = new_robot
                next_robot_id += 1
    
    if (len(robots) % 2) != 0:
        if allow_odd:
            print("WARNING: odd number of entrants. Inserting bye.")
            bye = robot.Robot(next_robot_id, "BYE", next_team_id);
        else:
            print("ERROR: off of number of entrants.")
            sys.exit(1)
                
    return robots

action_group = parser.add_mutually_exclusive_group()
action_group.add_argument("--prepare", action="store_true")
action_group.add_argument("--generate", action="store_true")
action_group.add_argument("--commit", action="store_true")

parser.add_argument("-f", "--file")
parser.add_argument("-n", "--round")
parser.add_argument("-o", "--output")
parser.add_argument("-i", "--id")
parser.add_argument("-l", "--left")
parser.add_argument("-r", "--right")
parser.add_argument('--test', action='store_true')
args = parser.parse_args()

if args.prepare:
    # Create a database and populate it
    # python swiss_generator.py -f <import.csv> -n 4 -o <output.db>
    db = db_manager.create_db(args.output, int(args.round))
    entrants = load_robots_from_csv(args.file, False)
    db_manager.add_robots(db, entrants)
    db_manager.close_db(db, (not args.test))
    
elif args.generate:
    # Generate a round of swiss format
    # python swiss_generator.py -f <input.db> -n 1
    db = db_manager.open_db(args.file)
    entrants, next_robot_id, next_fight_id = db_manager.load_existing_data(db)
    
    round_generator.generate(db, entrants, next_fight_id, int(args.round))
    
    db_manager.close_db(db, (not args.test))
    

elif args.commit:
    # Set the results of a fight
    # python swiss_generator.py -f <input.db> -i 1 -l 4 -r 1
    db = db_manager.open_db(args.file)
    entrants, next_robot_id, next_fight_id = db_manager.load_existing_data(db)
    
    db_manager.commit_result(db, int(args.id), int(args.left), int(args.right))
    
    db_manager.close_db(db, (not args.test))
    
    
else:
    print("Select: '--prepare', '--generate', '--commit'")
