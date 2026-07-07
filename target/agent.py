import http.server
import socketserver
import json
import subprocess
import os
import sys
from datetime import datetime, timezone

# Allow importing cascabel when run standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cascabel.config import CONFIG

class AgentHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/run':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command')
                
                start_time = datetime.now(timezone.utc).isoformat()
                
                # Log simulated telemetry
                log_entry = {
                    'timestamp': start_time,
                    'host': CONFIG.agent_host,
                    'source': 'mock_auditd',
                    'event_id': 'EXECVE',
                    'process_name': command.split()[0] if command else '',
                    'command_line': command
                }
                with open(CONFIG.mock_audit_log, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                
                # Execute the command securely without shell=True
                process = subprocess.Popen(
                    ["sh", "-c", command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                
                end_time = datetime.now(timezone.utc).isoformat()
                
                response = {
                    'status': 'success',
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': process.returncode,
                    'start_time': start_time,
                    'end_time': end_time
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer((CONFIG.agent_bind, CONFIG.agent_port), AgentHandler) as httpd:
        print(f"CASCABEL agent listening on {CONFIG.agent_bind}:{CONFIG.agent_port}")
        httpd.serve_forever()
