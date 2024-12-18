#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        sys.exit(1)

def setup_venv():
    print("Setting up virtual environment...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    if not os.path.exists("venv"):
        try:
            venv.create("venv", with_pip=True)
            # Install dependencies
            venv_pip = os.path.join("venv", "bin", "pip")
            run_command([venv_pip, "install", "-r", "requirements.txt"])
            print("Virtual environment created and dependencies installed")
        except Exception as e:
            print(f"Error setting up virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment already exists")

def setup_dns():
    print("Setting up DNS...")
    hosts_line = "127.0.0.1 go"
    hosts_path = "/etc/hosts"
    
    # Check if entry already exists
    with open(hosts_path, 'r') as f:
        if hosts_line in f.read():
            print("DNS entry already exists")
            return

    try:
        run_command(["sudo", "sh", "-c", f'echo "{hosts_line}" >> {hosts_path}'])
        print("DNS entry added successfully")
    except Exception as e:
        print(f"Error setting up DNS: {e}")
        print("Please manually add '127.0.0.1 go' to /etc/hosts")

def setup_database():
    print("Initializing database...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_flask = os.path.join(root_dir, "venv", "bin", "flask")
    
    # Create golinks directory if it doesn't exist
    golinks_dir = os.path.expanduser("~/.golinks")
    os.makedirs(golinks_dir, exist_ok=True)
    
    try:
        # Set the FLASK_APP environment variable
        os.environ["FLASK_APP"] = os.path.join(root_dir, "app.py")
        
        # Initialize database and run migrations
        run_command([venv_flask, "db", "upgrade"])
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

def create_systemd_service():
    print("Setting up systemd service...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(root_dir, "venv", "bin", "python3")
    app_path = os.path.join(root_dir, "app.py")
    
    service_content = f"""[Unit]
Description=GoLinks Local Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={root_dir}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart={venv_python} {app_path}
Restart=always

[Install]
WantedBy=multi-user.target
"""

    # Write service file
    service_path = "/etc/systemd/system/golinks.service"
    try:
        with open("/tmp/golinks.service", "w") as f:
            f.write(service_content)
        run_command(["sudo", "mv", "/tmp/golinks.service", service_path])
        run_command(["sudo", "systemctl", "daemon-reload"])
        run_command(["sudo", "systemctl", "enable", "golinks"])
        run_command(["sudo", "systemctl", "start", "golinks"])
        print("Service installed and started successfully")
    except Exception as e:
        print(f"Error setting up service: {e}")
        sys.exit(1)

def main():
    if os.geteuid() != 0:
        print("This script requires sudo privileges for DNS and service setup.")
        print("Please run: sudo python3 linux_install.py")
        sys.exit(1)

    # Check for requirements.txt
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(os.path.join(root_dir, "requirements.txt")):
        print("requirements.txt not found in the root directory")
        sys.exit(1)

    setup_venv()
    setup_dns()
    setup_database()
    create_systemd_service()
    print("\nInstallation complete! Access golinks at http://go/go")

if __name__ == "__main__":
    main()
