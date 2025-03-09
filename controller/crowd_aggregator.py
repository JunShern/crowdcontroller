#!/usr/bin/env python3
import asyncio
import json
import websockets
import time
from datetime import datetime
from collections import Counter
import logging
import os
import sys
import signal

# Import directly from the current directory
from controller import Controller, Action

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CrowdAggregator')

# Configuration
WEBSOCKET_URI = "wss://uvicorn-backendmain-production.up.railway.app/ws"
AGGREGATION_WINDOW = 5  # seconds

class CrowdAggregator:
    def __init__(self):
        self.command_counter = Counter()
        self.window_start_time = time.time()
        self.last_executed_command = None
        self.total_commands = 0
        self.commands_per_second = 0
        
        # Use the default Controller settings
        self.controller = Controller()
        
        # Flags for controlled shutdown
        self.running = True
        self.websocket_connected = False
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        self.running = False
        sys.exit(0)
        
    def record_command(self, command):
        """Record a command in the current aggregation window"""
        # Simply record the command without validation
        # The Controller will validate when executing
        self.command_counter[command] += 1
        self.total_commands += 1
        current_time = time.time()
        elapsed = current_time - self.window_start_time
        self.commands_per_second = self.total_commands / elapsed if elapsed > 0 else 0
        logger.debug(f"Recorded command: {command}")
            
    def execute_top_command(self):
        """Execute the most common command in the current window"""
        if not self.command_counter:
            logger.info("No commands to execute in this window")
            return None
        
        # Get the most common command
        top_command, count = self.command_counter.most_common(1)[0]
        total = sum(self.command_counter.values())
        
        try:
            # Execute the command directly - let the controller handle conversion
            logger.info(f"Executing top command: {top_command} (count: {count}, {count/total:.1%} of votes)")
            self.controller.execute(top_command)
            
            self.last_executed_command = {
                'command': top_command,
                'count': count,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            # Print a summary of all counts
            print("\nCommand Summary:")
            print(f"Total commands in window: {total}")
            for cmd, cnt in self.command_counter.most_common():
                percentage = (cnt / total) * 100 if total > 0 else 0
                print(f"{cmd}: {cnt} ({percentage:.1f}%)")
            print(f"\nEXECUTED: {top_command} with {count} votes ({(count/total)*100:.1f}%)")
            print("-" * 60)
                
            return top_command
        except Exception as e:
            logger.error(f"Error executing command {top_command}: {str(e)}")
            return None
            
    def reset_window(self):
        """Reset the aggregation window"""
        self.command_counter.clear()
        self.window_start_time = time.time()
        self.total_commands = 0
        self.commands_per_second = 0
        logger.info("Reset aggregation window")
        
    async def websocket_client(self):
        """Connect to the WebSocket server and process incoming commands"""
        while self.running:
            try:
                logger.info(f"Connecting to WebSocket server at {WEBSOCKET_URI}")
                async with websockets.connect(WEBSOCKET_URI) as websocket:
                    self.websocket_connected = True
                    logger.info("Connected to WebSocket server")
                    print("\nReady to receive commands...")
                    print("Commands will be aggregated and executed every 5 seconds")
                    print("Press Ctrl+C to exit\n")
                    
                    # Process messages
                    while self.running:
                        try:
                            message = await websocket.recv()
                            
                            try:
                                data = json.loads(message)
                                
                                # Extract the command from the message
                                if 'command' in data:
                                    command = data['command']
                                    print(f"\rReceived: {command}", end="")
                                    self.record_command(command)
                                else:
                                    logger.warning(f"Received message without command: {message}")
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse message: {message}")
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                                
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
                    
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                self.websocket_connected = False
                
            # Only attempt to reconnect if still running
            if self.running:
                logger.info("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
            else:
                break
                
    async def aggregation_timer(self):
        """Timer that triggers command execution at the end of each window"""
        while self.running:
            current_time = time.time()
            elapsed = current_time - self.window_start_time
            
            # Display time remaining
            remaining = max(0, AGGREGATION_WINDOW - elapsed)
            if int(remaining) != int(remaining + 0.1):  # Only print on whole seconds
                remaining_str = f"{remaining:.1f}"
                print(f"\rTime remaining: {remaining_str} seconds   ", end="")
                sys.stdout.flush()
            
            # Check if the window has elapsed
            if elapsed >= AGGREGATION_WINDOW:
                print("\n" + "=" * 60)
                logger.info("Aggregation window complete")
                
                # Execute the top command
                self.execute_top_command()
                
                # Reset for next window
                self.reset_window()
            
            # Short sleep to prevent CPU spinning
            await asyncio.sleep(0.1)
            
    async def run(self):
        """Run the main async components"""
        # Create tasks for websocket client and aggregation timer
        websocket_task = asyncio.create_task(self.websocket_client())
        timer_task = asyncio.create_task(self.aggregation_timer())
        
        try:
            # Wait for tasks to complete (they should run indefinitely)
            await asyncio.gather(websocket_task, timer_task)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")

def main():
    print("\n" + "=" * 70)
    print(f"CrowdAggregator - Command Aggregation Mode")
    print(f"Connecting to {WEBSOCKET_URI}")
    print(f"Aggregation window: {AGGREGATION_WINDOW} seconds")
    print("=" * 70 + "\n")
    
    # Create the aggregator
    aggregator = CrowdAggregator()
    
    try:
        # Run the aggregator
        asyncio.run(aggregator.run())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main() 