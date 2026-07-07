import http.server
import socketserver
import json
import subprocess
from datetime import datetime, timezone

PORT = 8080

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
                    'host': '127.0.0.1',
                    'source': 'mock_auditd',
                    'event_id': 'EXECVE',
                    'process_name': command.split()[0] if command else '',
                    'command_line': command
                }
                with open('mock_audit.log', 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                
                # Execute the command
                process = subprocess.Popen(
                    command,
                    shell=True,
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
    with socketserver.TCPServer(("", PORT), AgentHandler) as httpd:
        print(f"CASCABEL agent listening on port {PORT}")
        httpd.serve_forever()
