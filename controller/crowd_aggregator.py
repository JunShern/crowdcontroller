#!/usr/bin/env python3
import asyncio
import json
import websockets
import time
from datetime import datetime
from collections import Counter, deque
import logging
import os
import sys
import signal
import aiohttp
from aiohttp import web

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
AGGREGATION_WINDOW = 1  # seconds
WEB_PORT = 8080  # Port for visualization web server

# Path to the HTML template file (relative to this script)
HTML_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visualizer.html')

class CrowdAggregator:
    def __init__(self):
        self.command_counter = Counter()
        self.window_start_time = time.time()
        self.last_executed_command = None
        self.total_commands = 0
        self.commands_per_second = 0
        self.command_history = deque(maxlen=20)  # Store last 20 executed commands
        
        # Use the default Controller settings
        self.controller = Controller()
        
        # Flags for controlled shutdown
        self.running = True
        self.websocket_connected = False
        
        # For the visualization
        self.web_app = None
        self.visualization_clients = set()
        
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
        
        # Send this individual command to all visualization clients
        asyncio.create_task(self.broadcast_command(command))
        
        # Also broadcast the updated state
        asyncio.create_task(self.broadcast_state())
            
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
            
            # Create command record
            command_record = {
                'command': top_command,
                'count': count,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            # Store executed command in history
            self.last_executed_command = command_record
            self.command_history.appendleft(command_record)
            
            # Print a summary of all counts
            print("\nCommand Summary:")
            print(f"Total commands in window: {total}")
            for cmd, cnt in self.command_counter.most_common():
                percentage = (cnt / total) * 100 if total > 0 else 0
                print(f"{cmd}: {cnt} ({percentage:.1f}%)")
            print(f"\nEXECUTED: {top_command} with {count} votes ({(count/total)*100:.1f}%)")
            print("-" * 60)
            
            # Broadcast updated state including the executed command
            asyncio.create_task(self.broadcast_state())    
                
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
        
        # Broadcast the reset to all visualization clients
        asyncio.create_task(self.broadcast_state())
        
    async def websocket_client(self):
        """Connect to the WebSocket server and process incoming commands"""
        while self.running:
            try:
                logger.info(f"Connecting to WebSocket server at {WEBSOCKET_URI}")
                async with websockets.connect(WEBSOCKET_URI) as websocket:
                    self.websocket_connected = True
                    logger.info("Connected to WebSocket server")
                    print("\nReady to receive commands...")
                    print(f"Commands will be aggregated and executed every {AGGREGATION_WINDOW} seconds")
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
                
                # Broadcast state every second
                if self.visualization_clients:
                    await self.broadcast_state()
            
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
    
    async def broadcast_command(self, command):
        """Broadcast a single command to all visualization clients"""
        if not self.visualization_clients:
            return
            
        # Prepare command data
        data = {
            'type': 'command',
            'command': command,
            'timestamp': datetime.now().isoformat()
        }
        
        # Convert to JSON
        message = json.dumps(data)
        
        # Clients to remove
        to_remove = set()
        
        # Send to all clients
        for ws in self.visualization_clients:
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.error(f"Error sending command to visualization client: {str(e)}")
                to_remove.add(ws)
                
        # Remove closed connections
        for ws in to_remove:
            self.visualization_clients.remove(ws)
    
    async def broadcast_state(self):
        """Broadcast the current state to all visualization clients"""
        if not self.visualization_clients:
            return
            
        # Calculate time remaining
        current_time = time.time()
        elapsed = current_time - self.window_start_time
        remaining = max(0, AGGREGATION_WINDOW - elapsed)
        
        # Prepare state data
        state = {
            'type': 'state',
            'commands': dict(self.command_counter),
            'total': sum(self.command_counter.values()),
            'remaining': remaining,
            'last_executed': self.last_executed_command,
            'command_history': list(self.command_history)
        }
        
        # Convert to JSON
        message = json.dumps(state)
        
        # Clients to remove
        to_remove = set()
        
        # Send to all clients
        for ws in self.visualization_clients:
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.error(f"Error sending to visualization client: {str(e)}")
                to_remove.add(ws)
                
        # Remove closed connections
        for ws in to_remove:
            self.visualization_clients.remove(ws)
    
    async def handle_visualization_ws(self, request):
        """Handle WebSocket connections for visualization"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to clients
        self.visualization_clients.add(ws)
        logger.info(f"New visualization client connected, total: {len(self.visualization_clients)}")
        
        # Send initial state
        await self.broadcast_state()
        
        try:
            # Keep connection open
            async for msg in ws:
                # We don't expect messages from the client, but we need to keep the loop
                # to maintain the connection
                pass
        except Exception as e:
            logger.error(f"Visualization WebSocket error: {str(e)}")
        finally:
            # Remove from clients
            if ws in self.visualization_clients:
                self.visualization_clients.remove(ws)
            logger.info(f"Visualization client disconnected, remaining: {len(self.visualization_clients)}")
            
        return ws
    
    async def handle_index(self, request):
        """Serve the visualization HTML page"""
        try:
            with open(HTML_TEMPLATE_PATH, 'r') as f:
                html_content = f.read()
            return web.Response(text=html_content, content_type='text/html')
        except Exception as e:
            logger.error(f"Error reading HTML template: {str(e)}")
            return web.Response(text="Error loading visualization", status=500)
    
    def setup_web_app(self):
        """Set up the web application for visualization"""
        app = web.Application()
        app.router.add_get('/', self.handle_index)
        app.router.add_get('/visualize', self.handle_visualization_ws)
        self.web_app = app
            
    async def run(self):
        """Run the main async components"""
        # Set up the web app
        self.setup_web_app()
        
        # Start the web server
        runner = web.AppRunner(self.web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', WEB_PORT)
        await site.start()
        logger.info(f"Visualization server started at http://localhost:{WEB_PORT}")
        
        # Create tasks for websocket client and aggregation timer
        websocket_task = asyncio.create_task(self.websocket_client())
        timer_task = asyncio.create_task(self.aggregation_timer())
        
        try:
            # Wait for tasks to complete (they should run indefinitely)
            await asyncio.gather(websocket_task, timer_task)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")
        finally:
            # Clean up
            await runner.cleanup()

def main():
    print("\n" + "=" * 70)
    print(f"CrowdAggregator - Command Aggregation Mode with Visualization")
    print(f"Connecting to {WEBSOCKET_URI}")
    print(f"Aggregation window: {AGGREGATION_WINDOW} seconds")
    print(f"Visualization server at http://localhost:{WEB_PORT}")
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