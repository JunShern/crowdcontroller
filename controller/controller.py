import pyautogui
import time
from enum import Enum
from typing import List, Optional
from queue import Queue
from threading import Thread

class Action(Enum):
    # Character movement
    MOVE_UP = "W"
    MOVE_LEFT = "A"
    MOVE_DOWN = "S"
    MOVE_RIGHT = "D"
    
    # Mouse clicks
    LEFT_CLICK = "LEFT_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    
    # Cursor movement (relative)
    CURSOR_UP = "CURSOR_UP"
    CURSOR_DOWN = "CURSOR_DOWN"
    CURSOR_LEFT = "CURSOR_LEFT"
    CURSOR_RIGHT = "CURSOR_RIGHT"
    # Add more actions as needed

class Controller:
    def __init__(self, frequency: float, cursor_step: int, key_press_duration: float):
        """
        Initialize the controller.
        
        Args:
            frequency (float): How many times per second to process commands (Hz)
            cursor_step (int): Number of pixels to move cursor for each cursor movement action
            key_press_duration (float): Duration to hold keys and mouse buttons (seconds)
        """
        self.frequency = frequency
        self.cursor_step = cursor_step
        self.command_queue: Queue[Action] = Queue()
        self.is_running = False
        self._control_thread: Optional[Thread] = None
        
        # Safety feature
        pyautogui.FAILSAFE = True
        # Set a small delay between pyautogui commands
        pyautogui.PAUSE = 0.1
        
        # Key and mouse press duration in seconds
        self.key_press_duration = key_press_duration
    
    def start(self):
        """Start the controller in a separate thread."""
        if self.is_running:
            return
            
        self.is_running = True
        self._control_thread = Thread(target=self._control_loop)
        self._control_thread.daemon = True  # Thread will exit when main program exits
        self._control_thread.start()
    
    def stop(self):
        """Stop the controller."""
        self.is_running = False
        if self._control_thread:
            self._control_thread.join()
    
    def add_command(self, action: Action):
        """
        Add a command to the queue for processing.
        
        Args:
            action (Action): The action to be performed
        """
        self.command_queue.put(action)
    
    def _control_loop(self):
        """Main control loop that processes commands at the specified frequency."""
        period = 1.0 / self.frequency
        
        while self.is_running:
            loop_start = time.time()
            
            # Process any available commands
            self._process_next_command()
            
            # Sleep for remaining time to maintain frequency
            elapsed = time.time() - loop_start
            sleep_time = max(0, period - elapsed)
            time.sleep(sleep_time)
    
    def _process_next_command(self):
        """Process the next command in the queue if one exists."""
        if self.command_queue.empty():
            return
            
        action = self.command_queue.get()
        
        try:
            print(f"Processing action: {action}")
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
            self.stop()
        except Exception as e:
            print(f"Error processing action {action}: {str(e)}")

# Example usage:
if __name__ == "__main__":
    time.sleep(5)  # time to focus on the desired window

    controller = Controller(frequency=0.5, cursor_step=50, key_press_duration=0.1)
    
    # Example commands
    controller.add_command(Action.MOVE_UP)
    controller.add_command(Action.MOVE_DOWN)
    controller.add_command(Action.MOVE_LEFT)
    controller.add_command(Action.MOVE_RIGHT)
    controller.add_command(Action.CURSOR_RIGHT)  # Move cursor 20px right
    controller.add_command(Action.CURSOR_DOWN)   # Move cursor 20px down
    controller.add_command(Action.LEFT_CLICK)
    controller.add_command(Action.LEFT_CLICK)
    controller.add_command(Action.RIGHT_CLICK)
    controller.add_command(Action.LEFT_CLICK)
    controller.add_command(Action.LEFT_CLICK)
    controller.add_command(Action.RIGHT_CLICK)
    
    # Start the controller
    controller.start()
    
    # Let it run for a few seconds
    time.sleep(30)
    
    # Stop the controller
    controller.stop()
