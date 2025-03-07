import pyautogui
import time

# Set up safety feature - moving mouse to corner will stop script
pyautogui.FAILSAFE = True

# Add a small pause between actions
pyautogui.PAUSE = 0.5

def main():
    # Give user time to switch to the game window
    print("Starting in 5 seconds... Switch to your game window!")
    time.sleep(5)
    
    try:
        # Example actions
        # Move forward (press 'w' key for 2 seconds)
        print("Moving forward...")
        pyautogui.keyDown('w')
        time.sleep(2)
        pyautogui.keyUp('w')
        
        # Turn right (press 'd' key for 1 second)
        print("Turning right...")
        pyautogui.keyDown('d')
        time.sleep(1)
        pyautogui.keyUp('d')
        
        # Click at current mouse position
        print("Clicking mouse...")
        pyautogui.click()
        
        # Move mouse relative to current position
        print("Moving mouse...")
        pyautogui.moveRel(100, 0, duration=1)  # Move right 100 pixels
        
    except pyautogui.FailSafeException:
        print("Script stopped by failsafe (mouse moved to corner)")
    except KeyboardInterrupt:
        print("Script stopped by user (Ctrl+C)")

if __name__ == "__main__":
    main()
