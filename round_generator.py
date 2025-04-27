import random
import sys

import db_manager
import robot

def generate_pair(db, entrants, selected_robots, all_ids, robot_id, in_depth):
    """
    TOO

    :param this_uid:
    :param this_robot:
    :return:
    """
    
    robot_obj = entrants[robot_id]

    # Push to stack of selected bots
    selected_robots.append(robot_id)

    # These are used to compute the set of robots that this robot cannot fight
    team = db_manager.get_teammates(db, robot_id)
    fights = robot_obj.fights
    
    invalid_selections = []

    # TODO: something other than while True...
    # TODO: need to keep track of the number of matches created (i.e. stack depth), should be 1/2 the number of entrants
    while True:
        # We do not want to match this robot against:
        #    This robot's teammates
        #    Robots that this robot is already fighting
        #    Any robots that have already been selected in this round
        #    Any robots that we tried but resulted in invalid fights later on
        constraints = team + fights + selected_robots + invalid_selections
        
        available_bots = list(set(all_ids) - set(constraints))
        bots_str = " ".join(str(x) for x in available_bots)
        print(f"   ID {robot_id} can fight {bots_str}")

        if len(available_bots) == 0:
            # There are no possible selections for this fight - return False
            # Pop from stack of selected bots
            selected_robots.pop()
            print(f"No matches for UID {robot_id}")
            return False
        else:
            candidate_opponent = random.choice(available_bots)
            selected_robots.append(candidate_opponent)
            available_bots.remove(candidate_opponent)

            if len(available_bots) == 0:
                if len(all_ids) // 2 == in_depth:
                    # No more available bots, this must mean this is a valid solution
                    print(f"      ID {robot_id} is fighting {candidate_opponent}")
                    return True
                else:
                    # We ran out of valid matchups before we allocated all matchups
                    print(f"ran out of matchups when allocating for ID {robot_id} at depth {in_depth}")
                    return False
            else:
                # There are still more fights to generate
                next_id = random.choice(available_bots + invalid_selections)

                if generate_pair(db, entrants, selected_robots, all_ids, next_id, in_depth + 1):
                    # All fights generated after this one were okay, we can lock in this fight now
                    print(f"      ID {robot_id} is fighting {candidate_opponent}")
                    return True
                else:
                    # If we select this fight, then at least one robot later does not have any valid opponents
                    # We need to roll back and select a different candidate
                    selected_robots.pop()
                    invalid_selections.append(candidate_opponent)

def make_pairs(lst):
    """

    :param lst: a list (with even number of items)
    :return: a list of pairs
    """
    for i in range(0, len(lst), 2):
        yield lst[i:i+2]

def generate(db, entrants, next_fight_id, round_num):
    """
    TODO
    
    :param db: sqlite3.Connection object containing robot and fight information
    :round_num: integer round number
    :entrants: dictionary mapping 
    """

    # Get the current scores of each robot
    # select name, (round_1 + round_2 + round_3 + round_4 + round_5 + round_6) as score from robot
        
    cur = db.cursor()
    robots_list = []
    
    print(f"Generate fights for round {round_num}")
    
    for robot_id, robot_obj in entrants.items():
        robots_list.append((robot_id, robot_obj.score))
    
    print(robots_list)
    
    if round_num == 1:
        # Randomise the order if no fights have taken place yet
        print("random")
        random.shuffle(robots_list)
    else:  
        # Sort robots by their score
        print("sorting")
        # TODO: randomise the order of the robots sharing scores
        sorted_robots_list = sorted(robots_list, key=lambda tup: -tup[1])
    print(sorted_robots_list)
    
    robot_id_list = []
    for robot in sorted_robots_list:
        robot_id_list.append(robot[0])
    
    half_len = int(len(robot_id_list)/2)    
    top_half = robot_id_list[:half_len]
    bottom_half = robot_id_list[half_len:]
    
    print(f"top half: {top_half}")
    print(f"bottom_half: {bottom_half}")

    selected_robots = []
    fights_to_add = []

    if not generate_pair(db, entrants, selected_robots, top_half, random.choice(top_half), 1):
        print(f"ERROR: could not generate a valid set of fights for the top half of round {round_num}")
        db_manager.close_db(db, False)
        sys.exit(1)
    
    # Now we need to update the robot instances with their matchups
    for fight in list(make_pairs(selected_robots)):
        print(f"Fight: {fight[0]} vs {fight[1]}")
        
        l_robot = entrants[fight[0]]
        l_robot.add_fight(fight[1])
        entrants[fight[0]] = l_robot
        
        r_robot = entrants[fight[1]]
        l_robot.add_fight(fight[0])
        entrants[fight[1]] = l_robot
        
        fights_to_add.append((next_fight_id, round_num, fight[0], fight[1]))
        
        next_fight_id += 1

    selected_robots = []
    
    if not generate_pair(db, entrants, selected_robots, bottom_half, random.choice(bottom_half), 1):
        print(f"ERROR: could not generate a valid set of fights for the bottom half of round {round_num}")
        db_manager.close_db(db, False)
        sys.exit(1)
    
    # Now we need to update the robot instances with their matchups
    for fight in list(make_pairs(selected_robots)):
        print(f"Fight: {fight[0]} vs {fight[1]}")
        
        l_robot = entrants[fight[0]]
        l_robot.add_fight(fight[1])
        entrants[fight[0]] = l_robot
        
        r_robot = entrants[fight[1]]
        l_robot.add_fight(fight[0])
        entrants[fight[1]] = l_robot
        
        fights_to_add.append((next_fight_id, round_num, fight[0], fight[1]))
        
        next_fight_id += 1
    
    db_manager.add_fights(db, fights_to_add)
    