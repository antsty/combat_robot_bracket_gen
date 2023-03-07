# combat_robot_bracket_gen
A compilation of scripts designed to generate various tournament brackets for combat robot events.

All scripts take as an input a CSV file with 3 columns: "Roboteer", "Robot" and "Tech Checked". Tech Checked must be a 'Y' (capital Y) if a robot is to be considered for generation.

# de_generator.py
Script to generate double elimination tournament brackets, intended for use in conjunction with Challonge.

de_generator.py -f <input .csv> -o <output .txt>

# fn_generator.py
Script to generate fight night format rounds.

fn_generator.py -f <input .csv> -o <output .txt> -r <rounds (integer)>
