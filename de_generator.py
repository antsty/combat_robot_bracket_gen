import argparse
import csv
import random

# Global values
num_robots = 0
num_bye = 0

parser = argparse.ArgumentParser (prog="Double Elimination Generator",
                                  description="Read an input CSV and output a double elimination tournament bracket",
                                  epilog="")


def read_entrants(file_name):
    """
    Read a CSV file, returning a dictionary mapping roboteers to their check checked robots

    :param file_name: CSV file, with "Roboteer", "Robot" and "Tech Checked"
    :return: a dictionary mapping a roboteer to a list of their robots
    """
    global num_robots
    the_entrants = {}
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            the_robot_name = row["Robot"].strip(' "')
            the_roboteer_name = row["Roboteer"].strip()
            the_techchecked_name = row["Tech Checked"].strip()
            if the_techchecked_name == "Y":
                num_robots += 1
                # Create a blob representing robot data
                the_robot_blob = {"Name": the_robot_name,
                                  "Random": random.uniform(0, 1),
                                  "Group": ""}
                if the_roboteer_name in the_entrants:
                    the_entrants[the_roboteer_name].append(the_robot_blob)
                else:
                    the_entrants[the_roboteer_name] = [the_robot_blob]
    return the_entrants


def add_byes(robots, group_size):
    """

    :param robots:
    :param group_size:
    :return:
    """

    global num_robots, num_bye

    while not float(group_size).is_integer():
        num_bye += 1
        the_robot_blob = {"Name": f"bye_{num_bye}",
                          "Random": 2,
                          "Group": ""}
        if "bye" in robots:
            robots["bye"].append(the_robot_blob)
        else:
            robots["bye"] = [the_robot_blob]
        group_size = (num_robots + num_bye) / 4

    return num_bye


def sort_robots(the_team, the_index):
    """

    :param the_entrants: a dictionary mapping a roboteer to a list of their robots
    :param the_index:
    :return: a list of roboteers, sorted by the number of robots on their team, largest team first
    """
    return sorted(the_team, key=lambda k: k[the_index], reverse=False)


def sort_teams(the_robots, the_index):
    """

    :param the_robots:
    :param the_index:
    :return:
    """

    sorted_robots = the_robots

    for team_name, team in the_robots.items():
        sorted_team = sort_robots(team, the_index)
        sorted_robots[team_name] = sorted_team

    return sorted_robots


def assign_groups(robots):
    """

    :param robots:
    :return:
    """

    group = 1  # rotate 1 -> 2 -> 3 -> 4 = A -> C -> B -> D
    for team_name in robots:
        for idx, robot in enumerate(robots[team_name]):
            match group:
                case 1:
                    robots[team_name][idx]["Group"] = "A"
                    group += 1
                case 2:
                    robots[team_name][idx]["Group"] = "C"
                    group += 1
                case 3:
                    robots[team_name][idx]["Group"] = "B"
                    group += 1
                case 4:
                    robots[team_name][idx]["Group"] = "D"
                    group = 1
                case _:
                    print ("Problem with assigning robots")


def make_bracket(robots):
    group_a = []
    group_b = []
    group_c = []
    group_d = []

    for team_name, team in robots.items():
        for robot in team:
            match robot["Group"]:
                case "A":
                    group_a.append(robot)
                case "B":
                    group_b.append(robot)
                case "C":
                    group_c.append(robot)
                case "D":
                    group_d.append(robot)
                case _:
                    print ("Problem with assigning robots")

    group_a = sort_robots(group_a, "Random")
    group_b = sort_robots(group_b, "Random")
    group_c = sort_robots(group_c, "Random")
    group_d = sort_robots(group_d, "Random")

    return group_a + group_b + group_c + group_d


def write_output(filename, the_bracket):
    """

    :param filename:
    :param the_bracket:
    :return:
    """
    with open (filename, 'w') as fh:
        for robot in the_bracket:
            fh.write(f"{robot['Name']}\n")


parser.add_argument("-f", "--file")
parser.add_argument("-o", "--output")
parser.add_argument("-d", "--debug", action="store_true")
args = parser.parse_args()

# Parse input data
entrants = read_entrants(args.file)

# Group calculation
group_size = num_robots / 4
print(f"Read in {num_robots} robots, initial group size {group_size}")
byes = add_byes(entrants, group_size)
print(f"Added {byes} byes")

# Sort robots in their teams
sorted_entrants = sort_teams(entrants, "Random")

# Assign groups to robots
assign_groups(sorted_entrants)

# Produce final bracket list
bracket = make_bracket(sorted_entrants)

write_output(args.output, bracket)

if args.debug:
    for robot in bracket:
        print(f"Robot: {robot['Name']}, Group: {robot['Group']}")
