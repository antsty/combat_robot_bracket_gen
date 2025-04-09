import argparse
import csv
import random
import sys 

# Global values
num_robots = 0
has_melees = False

parser = argparse.ArgumentParser(prog="Fight Night Generator",
                                 description="Read an input CSV and output a list of fight night rounds",
                                 epilog="")


def read_entrants(the_file):
    """
    Read a CSV file, returning a dictionary mapping roboteers to their check checked robots

    :param the_file: CSV file, with "Roboteer", "Robot" and "Tech Checked"
    :return: a dictionary mapping a roboteer to a list of their robots
    """
    global num_robots
    the_entrants = {}
    with open(the_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            the_robot_name = row["Robot"].strip(' "')
            the_roboteer_name = row["Roboteer"].strip()
            the_techchecked_name = row["Tech Checked"].strip()
            if the_techchecked_name == "Y":
                num_robots += 1
                # Create a blob representing robot data
                the_robot_blob = {"Name": the_robot_name,
                                  "Team": [],
                                  "Fights": []}
                if the_roboteer_name in the_entrants:
                    the_entrants[the_roboteer_name].append(the_robot_blob)
                else:
                    the_entrants[the_roboteer_name] = [the_robot_blob]
    return the_entrants


def create_master_data_struct(the_entrants):
    """

    :param the_entrants: a dictionary mapping a roboteer to a list of their robots
    :return: a dictionary mapping a UID to a struct representing a single robot
    """
    uid = 1
    output = {}
    for the_roboteer, the_robots in the_entrants.items():
        team_uids_root = uid
        team_uids = list(range(team_uids_root, team_uids_root + len(the_robots)))
        for the_robot in the_robots:
            the_robot["Team"] = team_uids
            output[uid] = the_robot
            uid += 1
    return output


def make_pairs(lst):
    """

    :param lst: a list (with even number of items)
    :return: a list of pairs
    """
    for i in range(0, len(lst), 2):
        yield lst[i:i+2]


# TODO: make this function handle cases where robots have to have more than one melee
def generate_round(the_entrants, selected_for_melees, round_no, attempt_no):
    """

    :param the_entrants: a dictionary mapping a UID to a struct representing a single robot.
    :param selected_for_melees: a list of UIDs for robots taht have been selected for melees.
    :param round_no: integer round number
    :param attempt_no: integer attempt number
    :return: a list of 3-tuples representing fights for this round; updated list of UIDs for bots selected for melees; updated dictionary mapping a UID to a struct representing a single robot. 
    """
    global num_robots, has_melees

    # Local copy to make sure we can mutate without affecting global data
    out_entrants = the_entrants
    out_selected_for_melees = selected_for_melees
    print(num_robots)
    start_uid = random.randint(1, num_robots)
    all_uids = list(range(1, num_robots + 1))
    # Stack - push when a robot is selected for a fight
    selected_robots = []
    final_selected_robots = []
    selected_for_melee_this_round = 0
        
    if has_melees:
        # if melees are allowed, then remove one bot that hasn't been selected for a melee yet from the list,
        # so regular generation can succeed. Afterwards, we'll try to fit this robot into a valid melee (i.e. the other robots also haven't had a melee)
        available_bots = list(set(all_uids) - set(out_selected_for_melees))
        selected_for_melee_this_round = random.choice(available_bots)
        
    def generate_pair(this_uid, this_robot, in_depth):
        """

        :param this_uid:
        :param this_robot:
        :return:
        """

        # Push to stack of selected bots
        selected_robots.append(this_uid)

        # These are used to compute the set of robots that this robot cannot fight
        this_team = this_robot["Team"]
        this_fights = this_robot["Fights"]
        invalid_selections = []

        # TODO: something other than while True...
        # TODO: need to keep track of the number of matches created (i.e. stack depth), should be 1/2 the number of entrants
        while True:
            # We do not want to match this robot against:
            #    This robot's teammates
            #    Robots that this robot is already fighting
            #    Any robots that have already been selected in this round
            #    Any robots that we tried but resulted in invalid fights later on
            this_constraints = this_team + this_fights + selected_robots + invalid_selections
            if selected_for_melee_this_round != 0:
                this_constraints.append (selected_for_melee_this_round)
            available_bots = list(set(all_uids) - set(this_constraints))
            bots_str = " ".join(str(x) for x in available_bots)
            print(f"   ID {this_uid} can fight {bots_str}")

            if len(available_bots) == 0:
                # There are no possible selections for this fight - return False
                # Pop from stack of selected bots
                selected_robots.pop()
                print(f"No matches for UID {this_uid}")
                return False
            else:
                candidate_opponent = random.choice(available_bots)
                selected_robots.append(candidate_opponent)
                available_bots.remove(candidate_opponent)

                if len(available_bots) == 0:
                    if num_robots // 2 == in_depth:
                        # No more available bots, this must mean this is a valid solution
                        print(f"      ID {this_uid} is fighting {candidate_opponent}")
                        return True
                    else:
                        # We ran out of valid matchups before we allocated all matchups
                        print(f"ran out of matchups when allocating for ID {this_uid} at depth {in_depth}")
                        return False
                else:
                    # There are still more fights to generate
                    next_start_uid = random.choice(available_bots + invalid_selections)

                    if generate_pair(next_start_uid, out_entrants[next_start_uid], in_depth + 1):
                        # All fights generated after this one were okay, we can lock in this fight now
                        print(f"      ID {this_uid} is fighting {candidate_opponent}")
                        return True
                    else:
                        # If we select this fight, then at least one robot later does not have any valid opponents
                        # We need to roll back and select a different candidate
                        selected_robots.pop()
                        invalid_selections.append(candidate_opponent)
    
    if not generate_pair(start_uid, out_entrants[start_uid], 1):
        print(f"Error: could not generate a valid set of fights for round {round_no}, attempt {attempt_no}")
        return [], selected_for_melees, the_entrants, False

    round_fights = []
    has_allocated_melee = False
    
    # Now we need to update the robot structs with their matchups
    for fight in list(make_pairs(selected_robots)):
        out_entrants[fight[0]]["Fights"].append(fight[1])
        out_entrants[fight[1]]["Fights"].append(fight[0])
        
        third_bot = "="
        
        # allocate a melee if required
        if has_melees and not has_allocated_melee:
            # A valid melee is when:
            #  - both opponents in the 1v1 have not been selected for a melee
            #  - the candidate melee bot has not fought either 1v1 opponent
            selected_opponents_available = not (fight[0] in out_selected_for_melees) and not (fight[1] in out_selected_for_melees)
            
            # Getting bots that we can't select
            candidate_melee_bot = out_entrants[selected_for_melee_this_round]
            candidate_team = candidate_melee_bot["Team"]
            candidate_fights = candidate_melee_bot["Fights"]
            
            this_constraints = candidate_team + candidate_fights
            available_bots = list(set(all_uids) - set(this_constraints))
            
            has_not_fought_opponents = (fight[0] in available_bots) and (fight[1] in available_bots)
            
            if selected_opponents_available and has_not_fought_opponents:
                # This is a valid melee
                out_selected_for_melees.append(selected_for_melee_this_round)
                out_selected_for_melees.append(fight[0])
                out_selected_for_melees.append(fight[1])
                
                # Updating the 1v1 opponent data
                out_entrants[fight[0]]["Fights"].append(selected_for_melee_this_round)
                out_entrants[fight[1]]["Fights"].append(selected_for_melee_this_round)
                
                # Updating the melee candidate data
                out_entrants[selected_for_melee_this_round]["Fights"].append(fight[0])
                out_entrants[selected_for_melee_this_round]["Fights"].append(fight[1])
                
                third_bot = out_entrants[selected_for_melee_this_round]["Name"]
                
                has_allocated_melee = True

        # Pretty print fights
        round_fights.append((out_entrants[fight[0]]["Name"], out_entrants[fight[1]]["Name"], third_bot))
    
    if has_melees and not has_allocated_melee:
        print(f"Could not generate a valid melee for round {round_no}, attempt {attempt_no}")
        return [], selected_for_melees, the_entrants, False
        

    print(f"Successfully generated round {round_no}, attempt {attempt_no}")
    return round_fights, out_selected_for_melees, out_entrants, True


def write_output(filename, the_fights):
    """

    :param filename: file to write to
    :param the_fights: list of fights
    :return:
    """
    with open(filename, 'w') as fh:
        for fight in the_fights:
            if fight[0] == "=":
                fh.write("\n==============================================\n\n")
            elif fight[2] == "=":
                fh.write(f"1v1: {fight[0]} vs {fight[1]}\n")
            else:
                fh.write(f"MELEE: {fight[0]} vs {fight[1]} vs {fight[2]}\n")

parser.add_argument("-f", "--file")
parser.add_argument("-o", "--output")
parser.add_argument("-r", "--rounds")
parser.add_argument("-m", "--melees", action="store_true")
args = parser.parse_args()

# Parse input data
entrants = read_entrants(args.file)

if (num_robots % 2) != 0 and not args.melees:
    print("Cannot generate rounds for odd numbers of competitors")
    sys.exit(1)

has_melees = args.melees and (num_robots % 2) != 0

# Create master data structure
master_data = create_master_data_struct(entrants)
all_fights = []
selected_for_melees = []

for this_round in range(1, int(args.rounds)+1):
    max_attempts = 5
    for this_attempt in range (1, max_attempts + 1):
        fights, selected_for_melees, master_data, success = generate_round(master_data, selected_for_melees, this_round, this_attempt)
        if success:
            all_fights += fights
            all_fights += [("=", "=", "=")]
            break
        else:
            if this_attempt == max_attempts:
                print(f"Error: Failed fight night generation after {max_attempts} attempts for round {this_round}")
                sys.exit(1)

write_output(args.output, all_fights)
