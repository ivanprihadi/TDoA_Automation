"""
Recorder Manager Module
Handles SSH connections and remote recording on Raspberry Pi
"""

import paramiko
import scp
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from loguru import logger  # ✅ ADD THIS
import json
from dataclasses import dataclass


@dataclass
class ReceiverConfig:
    """Configuration for a single receiver"""
    id: str
    ip: str
    port: int
    username: str
    location: str
    latitude: float
    longitude: float


class RecorderManager:
    """
    Manages SSH connections to Raspberry Pi receivers
    Handles: SSH auth, remote execution, file transfer
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize RecorderManager
        
        Args:
            config_path: Path to JSON config file
        """
        self.receivers: Dict[str, Dict] = {}
        self.ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.scp_clients: Dict[str, scp.SCPClient] = {}
        self.config_path = config_path
        
        logger.info("RecorderManager initialized")
    
    def load_receivers_config(self, config_dict: Dict) -> None:
        """
        Load receiver configuration from dict
        
        Args:
            config_dict: Configuration dictionary with 'receivers' key
        """
        try:
            receivers_list = config_dict.get('network', {}).get('receivers', [])
            
            for rx in receivers_list:
                self.receivers[rx['id']] = {
                    'ip': rx['ip'],
                    'port': rx.get('port', 22),
                    'username': rx.get('username', 'pi'),
                    'location': rx.get('location', ''),
                    'latitude': rx.get('latitude', 0.0),
                    'longitude': rx.get('longitude', 0.0),
                }
            
            logger.info(f"Loaded {len(self.receivers)} receiver configurations")
            
        except Exception as e:
            logger.error(f"Error loading receiver config: {str(e)}")
            raise
    
    def connect(self, receiver_id: str, 
                private_key_path: str = None,
                timeout: int = 30) -> bool:
        """
        Connect to a single receiver via SSH
        
        Args:
            receiver_id: ID of receiver (e.g., 'RX1')
            private_key_path: Path to SSH private key
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection successful
        """
        try:
            if receiver_id not in self.receivers:
                logger.error(f"Receiver {receiver_id} not in configuration")
                return False
            
            rx_config = self.receivers[receiver_id]
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH key or password
            if private_key_path:
                client.connect(
                    hostname=rx_config['ip'],
                    port=rx_config['port'],
                    username=rx_config['username'],
                    key_filename=private_key_path,
                    timeout=timeout,
                    look_for_keys=True,
                    allow_agent=True
                )
            else:
                # Fallback: try to connect with key from default location
                client.connect(
                    hostname=rx_config['ip'],
                    port=rx_config['port'],
                    username=rx_config['username'],
                    look_for_keys=True,
                    allow_agent=True,
                    timeout=timeout
                )
            
            self.ssh_clients[receiver_id] = client
            logger.info(f"Connected to {receiver_id} ({rx_config['ip']})")
            
            return True
            
        except paramiko.AuthenticationException:
            logger.error(f"SSH authentication failed for {receiver_id}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH error connecting to {receiver_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to {receiver_id}: {str(e)}")
            return False
    
    def connect_all(self, private_key_path: str = None) -> Dict[str, bool]:
        """
        Connect to all receivers
        
        Args:
            private_key_path: Path to SSH private key
            
        Returns:
            Dictionary of {receiver_id: success_status}
        """
        results = {}
        
        for receiver_id in self.receivers.keys():
            results[receiver_id] = self.connect(receiver_id, private_key_path)
            time.sleep(0.5)  # Small delay between connections
        
        logger.info(f"Connection results: {sum(results.values())}/{len(results)} successful")
        
        return results
    
    def execute_command(self, receiver_id: str, command: str,
                       get_output: bool = True) -> Tuple[int, str, str]:
        """
        Execute command on remote receiver
        
        Args:
            receiver_id: ID of receiver
            command: Command to execute
            get_output: Whether to capture output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            if receiver_id not in self.ssh_clients:
                logger.error(f"No active connection to {receiver_id}")
                return (1, "", "Not connected")
            
            client = self.ssh_clients[receiver_id]
            
            logger.debug(f"Executing on {receiver_id}: {command}")
            
            stdin, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_str = stdout.read().decode('utf-8') if get_output else ""
            stderr_str = stderr.read().decode('utf-8') if get_output else ""
            
            logger.debug(f"Command completed with exit code: {exit_code}")
            
            return (exit_code, stdout_str, stderr_str)
            
        except Exception as e:
            logger.error(f"Error executing command on {receiver_id}: {str(e)}")
            return (1, "", str(e))
    
    def start_recording(self, receiver_id: str,
                       fref_mhz: float = 100.0,  # ✅ FIXED INDENTATION
                       fcari_mhz: float = 93.8,
                       loops: int = 1) -> bool:
        """
        Start recording on a receiver using pewaktu_new
        
        Args:
            receiver_id: ID of receiver
            fref_mhz: Reference frequency in MHz
            fcari_mhz: Target frequency in MHz
            loops: Number of recording loops
            
        Returns:
            True if recording started successfully
        """
        try:
            remote_output_dir = "/home/pi/recorded_data"
            
            # Build command sesuai spesifikasi penelitian
            command = (
                f"/home/pi/pewaktu_new "
                f"--fref {fref_mhz*1e6:.0f} "
                f"--fcari {fcari_mhz*1e6:.0f} "
                f"--loop {loops}"
            )
            
            logger.info(f"Starting recording on {receiver_id}")
            logger.info(f"  Freq: {fref_mhz}/{fcari_mhz} MHz, Loops: {loops}")
            logger.debug(f"Command: {command}")
            
            exit_code, stdout, stderr = self.execute_command(receiver_id, command)
            
            if exit_code == 0:
                logger.info(f"Recording started on {receiver_id}")
                return True
            else:
                logger.error(f"Failed to start recording on {receiver_id}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting recording on {receiver_id}: {str(e)}")
            return False
    
    def wait_for_recording(self, receiver_id: str,
                          estimated_duration: int = 12,
                          check_interval: int = 2) -> bool:
        """
        Wait for recording to complete on receiver
        
        Args:
            receiver_id: ID of receiver
            estimated_duration: Expected duration in seconds
            check_interval: Interval to check status
            
        Returns:
            True if recording completed successfully
        """
        try:
            elapsed = 0
            expected_duration = estimated_duration + 5  # Add buffer
            
            while elapsed < expected_duration:
                # Check if pewaktu_new process is still running
                exit_code, stdout, stderr = self.execute_command(
                    receiver_id,
                    "pgrep -f pewaktu_new"
                )
                
                if exit_code != 0:  # Process not running
                    logger.info(f"Recording completed on {receiver_id}")
                    return True
                
                logger.debug(f"Waiting for recording on {receiver_id}... ({elapsed}s)")
                time.sleep(check_interval)
                elapsed += check_interval
            
            logger.warning(f"Recording timeout on {receiver_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for recording on {receiver_id}: {str(e)}")
            return False
    
    def list_remote_files(self, receiver_id: str,
                         remote_path: str = "/home/pi/recorded_data/") -> List[str]:
        """
        List files in remote directory
        
        Args:
            receiver_id: ID of receiver
            remote_path: Path to list
            
        Returns:
            List of filenames
        """
        try:
            exit_code, stdout, stderr = self.execute_command(
                receiver_id,
                f"ls -lah {remote_path}"
            )
            
            if exit_code == 0:
                files = [line.split()[-1] for line in stdout.split('\n') if line]
                logger.debug(f"Files on {receiver_id}: {files}")
                return files
            else:
                logger.error(f"Failed to list files on {receiver_id}: {stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing files on {receiver_id}: {str(e)}")
            return []
    
    def download_file(self, receiver_id: str,
                     remote_file: str,
                     local_path: str = "./output/") -> bool:
        """
        Download file from receiver to local computer
        
        Args:
            receiver_id: ID of receiver
            remote_file: Full path to remote file
            local_path: Local destination path
            
        Returns:
            True if download successful
        """
        try:
            # Ensure local directory exists
            local_dir = Path(local_path)
            local_dir.mkdir(parents=True, exist_ok=True)
            
            if receiver_id not in self.ssh_clients:
                logger.error(f"No active connection to {receiver_id}")
                return False
            
            client = self.ssh_clients[receiver_id]
            
            # Use SCP to download file
            with scp.SCPClient(client.get_transport()) as scp_client:
                scp_client.get(remote_file, local_path, recursive=False)
            
            local_filename = Path(remote_file).name
            logger.info(f"Downloaded {remote_file} from {receiver_id} to {local_path}{local_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file from {receiver_id}: {str(e)}")
            return False
    
    def download_files(self, receiver_id: str,
                      remote_files: List[str],
                      local_path: str = "./output/") -> Dict[str, bool]:
        """
        Download multiple files from receiver
        
        Args:
            receiver_id: ID of receiver
            remote_files: List of remote file paths
            local_path: Local destination path
            
        Returns:
            Dictionary of {filename: success_status}
        """
        results = {}
        
        for remote_file in remote_files:
            results[remote_file] = self.download_file(receiver_id, remote_file, local_path)
            time.sleep(0.5)  # Delay between downloads
        
        return results
    
    def disconnect(self, receiver_id: str) -> None:
        """
        Disconnect from a receiver
        
        Args:
            receiver_id: ID of receiver
        """
        try:
            if receiver_id in self.ssh_clients:
                self.ssh_clients[receiver_id].close()
                del self.ssh_clients[receiver_id]
                logger.info(f"Disconnected from {receiver_id}")
        except Exception as e:
            logger.error(f"Error disconnecting from {receiver_id}: {str(e)}")
    
    def disconnect_all(self) -> None:  # ✅ FIXED INDENTATION
        """Disconnect from all receivers"""
        receiver_ids = list(self.ssh_clients.keys())
        
        for receiver_id in receiver_ids:
            self.disconnect(receiver_id)
        
        logger.info("Disconnected from all receivers")
    
    def __del__(self):
        """Cleanup on object deletion"""
        self.disconnect_all()


# Test script
if __name__ == "__main__":
    # Test configuration
    test_config = {
        'network': {
            'receivers': [
                {
                    'id': 'RX1',
                    'ip': '10.147.20.111',
                    'port': 22,
                    'username': 'pi',
                    'location': 'Kampus PENS',
                    'latitude': -7.2772222222,
                    'longitude': 112.7930555556
                }
            ]
        }
    }
    
    logger.info("Testing RecorderManager...")
    
    manager = RecorderManager()
    manager.load_receivers_config(test_config)
    
    # Test connection
    if manager.connect('RX1', private_key_path=None):
        logger.info("Connection test successful!")
        
        # Test command execution
        exit_code, stdout, stderr = manager.execute_command('RX1', 'uname -a')
        logger.info(f"System info: {stdout}")
    
    manager.disconnect_all()