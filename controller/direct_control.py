#!/usr/bin/env python3
import asyncio
import json
import websockets
import logging
import signal
import sys

# Import the controller
from controller import Controller, Action

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DirectControl')

# WebSocket URI for Railway
WEBSOCKET_URI = "wss://uvicorn-backendmain-production.up.railway.app/ws"

class DirectControl:
    def __init__(self):
        # Use Controller with default values
        self.controller = Controller()
        self.running = True
        self.total_commands = 0
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
    def handle_signal(self, sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        self.running = False
        sys.exit(0)
        
    def execute_command(self, command_str):
        """Execute a command using the controller"""
        try:
            # Convert string to Action enum and execute
            logger.info(f"Executing command: {command_str}")
            self.controller.execute(command_str)
            self.total_commands += 1
            
            # Print a status update every 10 commands
            if self.total_commands % 10 == 0:
                logger.info(f"Total commands executed: {self.total_commands}")
                
            return True
        except Exception as e:
            logger.error(f"Error executing command {command_str}: {str(e)}")
            return False
            
    async def websocket_client(self):
        """Connect to the WebSocket server and execute received commands"""
        while self.running:
            try:
                logger.info(f"Connecting to WebSocket server at {WEBSOCKET_URI}")
                async with websockets.connect(WEBSOCKET_URI) as websocket:
                    logger.info("Connected to WebSocket server")
                    print("\nReady to receive commands...")
                    print("Press Ctrl+C to exit\n")
                    
                    # Process messages
                    while self.running:
                        try:
                            message = await websocket.recv()
                            
                            try:
                                data = json.loads(message)
                                
                                # Extract and execute the command
                                if 'command' in data:
                                    command = data['command']
                                    print(f"\rExecuting: {command}", end="")
                                    self.execute_command(command)
                                else:
                                    logger.warning(f"Received message without command: {message}")
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse message: {message}")
                                
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
                    
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                
            # Only attempt to reconnect if still running
            if self.running:
                logger.info("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
            else:
                break

async def run():
    # Create the direct control instance
    direct_control = DirectControl()
    
    try:
        # Run the WebSocket client
        await direct_control.websocket_client()
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(f"DirectControl - No Aggregation Mode")
    print(f"Connecting to {WEBSOCKET_URI}")
    print("=" * 70 + "\n")
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 