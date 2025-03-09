import pyautogui
import time
from enum import Enum

class Action(Enum):
    # Character movement
    MOVE_UP = "MOVE_UP"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_RIGHT = "MOVE_RIGHT"
    
    # Mouse clicks
    LEFT_CLICK = "LEFT_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    
    # Cursor movement (relative)
    CURSOR_UP = "CURSOR_UP"
    CURSOR_DOWN = "CURSOR_DOWN"
    CURSOR_LEFT = "CURSOR_LEFT"
    CURSOR_RIGHT = "CURSOR_RIGHT"

class Controller:
    def __init__(self, cursor_step=50, key_press_duration=0.1):
        """
        Initialize the controller.
        
        Args:
            cursor_step (int): Number of pixels to move cursor for each cursor movement action
            key_press_duration (float): Duration to hold keys and mouse buttons (seconds)
        """
        # Safety feature
        pyautogui.FAILSAFE = True
        
        # Set a small delay between pyautogui commands
        pyautogui.PAUSE = 0.05
        
        # Configuration
        self.cursor_step = cursor_step
        self.key_press_duration = key_press_duration
        
        print(f"Controller initialized (cursor_step={cursor_step}, key_press_duration={key_press_duration})")
    
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
            
            # Handle mouse clicks with press duration
            elif action == Action.LEFT_CLICK:
                pyautogui.mouseDown(button='left')
                time.sleep(self.key_press_duration)
                pyautogui.mouseUp(button='left')
            elif action == Action.RIGHT_CLICK:
                pyautogui.mouseDown(button='right')
                time.sleep(self.key_press_duration)
                pyautogui.mouseUp(button='right')
            
            # Handle cursor movement
            elif action == Action.CURSOR_UP:
                pyautogui.moveRel(0, -self.cursor_step)
            elif action == Action.CURSOR_DOWN:
                pyautogui.moveRel(0, self.cursor_step)
            elif action == Action.CURSOR_LEFT:
                pyautogui.moveRel(-self.cursor_step, 0)
            elif action == Action.CURSOR_RIGHT:
                pyautogui.moveRel(self.cursor_step, 0)
                
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
    controller.execute(Action.CURSOR_RIGHT)
    time.sleep(0.5)
    controller.execute(Action.CURSOR_LEFT)
    time.sleep(0.5)
    controller.execute(Action.LEFT_CLICK)
    
    print("Test complete!")
