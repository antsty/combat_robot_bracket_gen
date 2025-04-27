"""
Robot class and associated methods
"""

class Robot:
    """
    Represents a single robot
    
    id: integer, unique ID
    name: string, name of the robot
    team_id: integer, team unique ID
    fights: list of integers, IDs of robots that this robot is fighting
    """

    def __init__(self, id, name, team_id):
        self.id = id
        self.name = name
        self.team_id = team_id
        self.fights = []
        self.score = 0
    
    def get_id(self):
        return self.id
        
    def get_name(self):
        return self.name
        
    def get_team_id(self):
        return self.team_id
    
    def add_fight(self, id):
        """
        Add a robot for this robot to fight against

        :id: integer, ID of the robot to fight
        
        return True if fight has been added, False otherwise
        """
        if id in self.fights:
            return False
    
        self.fights.append (id)
        
        return True

    def set_score(self, score):
        self.score = score
    def get_score(self):
        return self.score