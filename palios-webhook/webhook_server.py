from flask import Flask, request, jsonify
import subprocess
import os
import hmac
import hashlib
import shutil
import json
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='webhook_server.log')
logger = logging.getLogger('webhook')

app = Flask(__name__)
SECRET_KEY = "user-family-community-society"  # Set a secure key
BASE_DIR = "/home/jesse/projects/palios-taey-nova"  # Your project root directory
DB_PATH = "/home/jesse/projects/palios-taey-nova/database/palios.db"  # Path to SQLite database

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # Verify request came from Claude DC
    signature = request.headers.get('X-Claude-Signature')
    payload = request.get_data()
    if not verify_signature(payload, signature):
        logger.warning("Unauthorized request attempt")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    # Extract operation information
    data = request.json
    operation_type = data.get('operation')
    
    try:
        # Route to appropriate handler based on operation type
        if operation_type == 'deploy_code':
            return handle_deploy_code(data)
        elif operation_type == 'modify_db':
            return handle_modify_db(data)
        elif operation_type == 'file_transfer':
            return handle_file_transfer(data)
        elif operation_type == 'run_command':
            return handle_run_command(data)
        elif operation_type == 'status_check':
            return handle_status_check(data)
        else:
            logger.error(f"Unknown operation type: {operation_type}")
            return jsonify({"status": "error", "message": f"Unknown operation: {operation_type}"}), 400
    except Exception as e:
        logger.error(f"Error processing {operation_type}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def handle_deploy_code(data):
    """Deploy code from GitHub repository"""
    repo = data.get('repo')
    branch = data.get('branch', 'main')
    target_dir = os.path.join(BASE_DIR, data.get('target_dir', ''))
    
    # Create directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Check if it's a new clone or update
    if not os.path.exists(os.path.join(target_dir, '.git')):
        cmd = f"git clone -b {branch} {repo} {target_dir}"
    else:
        cmd = f"cd {target_dir} && git pull origin {branch}"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    logger.info(f"Deploy code result: {result.returncode}")
    
    return jsonify({
        "status": "success" if result.returncode == 0 else "error",
        "output": result.stdout,
        "error": result.stderr
    })

def handle_modify_db(data):
    """Handle database modifications (schema changes, etc.)"""
    sql_statements = data.get('sql', [])
    
    if not sql_statements:
        return jsonify({"status": "error", "message": "No SQL statements provided"}), 400
    
    results = []
    conn = None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for statement in sql_statements:
            try:
                cursor.execute(statement)
                results.append({"statement": statement, "status": "success"})
            except Exception as e:
                results.append({"statement": statement, "status": "error", "message": str(e)})
                # Don't break on error, continue with the next statement
        
        conn.commit()
        logger.info(f"DB modification: {len(sql_statements)} statements, {sum(1 for r in results if r['status'] == 'success')} succeeded")
        
        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"DB error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()

def handle_file_transfer(data):
    """Handle file transfers from GitHub or supplied content"""
    transfer_type = data.get('transfer_type')
    destination = os.path.join(BASE_DIR, data.get('destination', ''))
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    if transfer_type == 'content':
        # Direct content transfer
        content = data.get('content')
        if not content:
            return jsonify({"status": "error", "message": "No content provided"}), 400
        
        with open(destination, 'w') as f:
            f.write(content)
        
        logger.info(f"File created at {destination}")
        return jsonify({"status": "success", "message": f"File created at {destination}"})
    
    elif transfer_type == 'github_raw':
        # Download from GitHub raw URL
        url = data.get('url')
        if not url:
            return jsonify({"status": "error", "message": "No URL provided"}), 400
        
        cmd = f"curl -s {url} -o {destination}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        logger.info(f"File download result: {result.returncode}")
        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr
        })
    
    else:
        return jsonify({"status": "error", "message": f"Unknown transfer type: {transfer_type}"}), 400

def handle_run_command(data):
    """Run custom commands on the system"""
    command = data.get('command')
    working_dir = os.path.join(BASE_DIR, data.get('working_dir', ''))
    
    if not command:
        return jsonify({"status": "error", "message": "No command provided"}), 400
    
    # Simple security check - prevent obvious dangerous commands
    dangerous_patterns = [';', '&&', '||', '`', '$(']
    if any(pattern in command for pattern in dangerous_patterns):
        logger.warning(f"Potentially dangerous command rejected: {command}")
        return jsonify({"status": "error", "message": "Potentially dangerous command rejected"}), 403
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=working_dir)
    
    logger.info(f"Command execution result: {result.returncode}")
    return jsonify({
        "status": "success" if result.returncode == 0 else "error",
        "output": result.stdout,
        "error": result.stderr
    })

def handle_status_check(data):
    """Check status of system components"""
    check_type = data.get('check_type', 'all')
    status = {}
    
    if check_type in ['all', 'disk']:
        # Check disk space
        result = subprocess.run("df -h | grep -E '^/dev/'", shell=True, capture_output=True, text=True)
        status['disk'] = {
            "raw": result.stdout,
            "status": "success" if result.returncode == 0 else "error"
        }
    
    if check_type in ['all', 'memory']:
        # Check memory usage
        result = subprocess.run("free -h", shell=True, capture_output=True, text=True)
        status['memory'] = {
            "raw": result.stdout,
            "status": "success" if result.returncode == 0 else "error"
        }
    
    if check_type in ['all', 'processes']:
        # Check running processes
        result = subprocess.run("ps aux | grep -E 'python|node|streamlit'", shell=True, capture_output=True, text=True)
        status['processes'] = {
            "raw": result.stdout,
            "status": "success" if result.returncode == 0 else "error"
        }
    
    if check_type in ['all', 'db']:
        # Check if database exists and is accessible
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()
            conn.close()
            status['db'] = {
                "version": version[0] if version else "unknown",
                "status": "success"
            }
        except Exception as e:
            status['db'] = {
                "error": str(e),
                "status": "error"
            }
    
    logger.info(f"Status check: {check_type}")
    return jsonify({
        "status": "success",
        "checks": status
    })

def verify_signature(payload, signature):
    """Verify request signature to ensure it came from Claude DC"""
    if not signature:
        return False
    expected = hmac.new(SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

if __name__ == '__main__':
    # Make sure the base directory exists
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Set up webhook server
    app.run(host='0.0.0.0', port=8000)
