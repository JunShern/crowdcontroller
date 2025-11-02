import pyautogui
import time
from enum import Enum

class Action(Enum):
    # Character movement
    MOVE_UP = "MOVE_UP"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_RIGHT = "MOVE_RIGHT"

    # Game actions
    PICKAXE = "PICKAXE"
    WATER = "WATER"
    PROPOSE = "PROPOSE"
    YES = "YES"

class Controller:
    def __init__(self, key_press_duration=0.1, action_delay=0.05):
        """
        Initialize the controller.

        Args:
            key_press_duration (float): Duration to hold keys and mouse buttons (seconds)
            action_delay (float): Delay between actions in a sequence (seconds)
        """
        # Safety feature
        pyautogui.FAILSAFE = True

        # Set a small delay between pyautogui commands
        pyautogui.PAUSE = 0.05

        # Configuration
        self.key_press_duration = key_press_duration
        self.action_delay = action_delay

        print(f"Controller initialized (key_press_duration={key_press_duration}, action_delay={action_delay})")
    
    def execute(self, action):
        """
        Execute an action immediately.
        
        Args:
            action (Action): The action to be performed (or a string that can be converted to an Action)
        """
        # Convert string to Action if needed
        if isinstance(action, str):
            try:
                # Check if the string matches any Action name (not value)
                action = Action[action]
            except KeyError:
                # If not, try to see if it matches any Action value
                try:
                    action = Action(action)
                except ValueError:
                    print(f"Error: Invalid action '{action}'. Valid actions: {[a.name for a in Action]}")
                    return
        elif not isinstance(action, Action):
            print(f"Error: Invalid action type {type(action)}. Expected Action enum or string.")
            return
        
        try:
            print(f"Executing action: {action.name}")
            
            # Handle character movement
            if action == Action.MOVE_UP:
                pyautogui.keyDown('w')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('w')
            elif action == Action.MOVE_DOWN:
                pyautogui.keyDown('s')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('s')
            elif action == Action.MOVE_LEFT:
                pyautogui.keyDown('a')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('a')
            elif action == Action.MOVE_RIGHT:
                pyautogui.keyDown('d')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('d')

            # Handle game actions (number key + appropriate click sequences)
            elif action == Action.PICKAXE:
                # Press '1' key
                pyautogui.keyDown('1')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('1')
                time.sleep(self.action_delay)
                # Left click
                pyautogui.mouseDown(button='left')
                time.sleep(self.key_press_duration)
                pyautogui.mouseUp(button='left')
            elif action == Action.WATER:
                # Press '2' key
                pyautogui.keyDown('2')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('2')
                time.sleep(self.action_delay)
                # Left click
                pyautogui.mouseDown(button='left')
                time.sleep(self.key_press_duration)
                pyautogui.mouseUp(button='left')
            elif action == Action.PROPOSE:
                # Press '3' key
                pyautogui.keyDown('3')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('3')
                time.sleep(self.action_delay)
                # Right click
                pyautogui.mouseDown(button='right')
                time.sleep(self.key_press_duration)
                pyautogui.mouseUp(button='right')
            elif action == Action.YES:
                # Press 'Y' key
                pyautogui.keyDown('y')
                time.sleep(self.key_press_duration)
                pyautogui.keyUp('y')

        except pyautogui.FailSafeException:
            print("Failsafe triggered - mouse moved to corner")
        except Exception as e:
            print(f"Error processing action {action}: {str(e)}")

# Example usage (only runs if this file is executed directly)
if __name__ == "__main__":
    print("Testing Controller with some basic commands...")
    controller = Controller()

    # Give user time to switch to a window
    print("Starting in 5 seconds... Switch to the desired application window")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    # Test some actions
    controller.execute(Action.MOVE_UP)
    time.sleep(0.5)
    controller.execute(Action.MOVE_DOWN)
    time.sleep(0.5)
    controller.execute(Action.PICKAXE)
    time.sleep(0.5)
    controller.execute(Action.WATER)
    time.sleep(0.5)
    controller.execute(Action.PROPOSE)

    print("Test complete!")
