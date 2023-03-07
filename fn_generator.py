import argparse
import csv
import random
import sys

# Global values
num_robots = 0

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


def generate_round(the_entrants, round_no):
    """

    :param the_entrants: a dictionary mapping a UID to a struct representing a single robot.
    :param round_no: integer round number
    :return: a list of pairs representing fights for this round
    """
    global num_robots

    # Local copy to make sure we can mutate without affecting global data
    out_entrants = the_entrants

    start_uid = random.randint(1, num_robots)
    all_uids = list(range(1, num_robots + 1))
    # Stack - push when a robot is selected for a fight
    selected_robots = []

    def generate_pair(this_uid, this_robot):
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
        while True:
            # We do not want to match this robot against:
            #    This robot's teammates
            #    Robots that this robot is already fighting
            #    Any robots that have already been selected in this round
            #    Any robots that we tried but resulted in invalid fights later on
            this_constraints = this_team + this_fights + selected_robots + invalid_selections
            available_bots = list(set(all_uids) - set(this_constraints))

            if len(available_bots) == 0:
                # There are no possible selections for this fight - return False
                # Pop from stack of selected bots
                selected_robots.pop()
                return False
            else:
                candidate_opponent = random.choice(available_bots)
                selected_robots.append(candidate_opponent)
                available_bots.remove(candidate_opponent)

                if len(available_bots) == 0:
                    # No more available bots, this must mean this is a valid solution
                    return True
                else:
                    # There are still more fights to generate
                    next_start_uid = random.choice(available_bots)

                    if generate_pair(next_start_uid, out_entrants[next_start_uid]):
                        # All fights generated after this one were okay, we can lock in this fight now
                        return True
                    else:
                        # If we select this fight, then at least one robot later does not have any valid opponents
                        # We need to roll back and select a different candidate
                        selected_robots.pop()
                        invalid_selections.append(candidate_opponent)

    if not generate_pair(start_uid, out_entrants[start_uid]):
        print(f"Error: could not generate a valid set of fights for round {round_no}")
        sys.exit(1)

    round_fights = []

    # Now we need to update the robot structs with their matchups
    for fight in list(make_pairs(selected_robots)):
        out_entrants[fight[0]]["Fights"].append(fight[1])
        out_entrants[fight[1]]["Fights"].append(fight[0])

        # Pretty print fights
        round_fights.append((out_entrants[fight[0]]["Name"], out_entrants[fight[1]]["Name"]))

    return round_fights, out_entrants


def write_output(filename, the_fights):
    """

    :param filename: file to write to
    :param the_fights: list of fights
    :return:
    """
    with open(filename, 'w') as fh:
        for fight in the_fights:
            fh.write(f"{fight[0]} vs {fight[1]}\n")


parser.add_argument("-f", "--file")
parser.add_argument("-o", "--output")
parser.add_argument("-r", "--rounds")
args = parser.parse_args()

# Parse input data
entrants = read_entrants(args.file)

if (num_robots % 2) != 0:
    print("Cannot generate rounds for odd numbers of competitors")
    sys.exit(1)

# Create master data structure
master_data = create_master_data_struct(entrants)
all_fights = []

for this_round in range(1, int(args.rounds)+1):
    fights, master_data = generate_round(master_data, this_round)
    all_fights += fights
    all_fights += [("=", "=")]

write_output(args.output, all_fights)
