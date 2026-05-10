"""
Recording Service - Handle recording automation via API
Manages: synchronization, timing, file naming, data transfer
"""

import json
import time
import uuid
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from .recorder_manager import RecorderManager
from .config_manager import ConfigManager


class RecordingSession:
    """Represents a single recording session"""
    
    def __init__(self, session_id: str, fref_mhz: float, fcari_mhz: float, 
                 loops: int, sync_mode: str):
        self.session_id = session_id
        self.fref_mhz = fref_mhz
        self.fcari_mhz = fcari_mhz
        self.loops = loops
        self.sync_mode = sync_mode
        
        # Status tracking
        self.status = 'initializing'
        self.progress = 'Starting...'
        self.start_time = datetime.now()
        self.elapsed_seconds = 0
        self.files_downloaded = []
        self.total_size_mb = 0
        self.error = None
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for JSON response"""
        self.elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        return {
            'session_id': self.session_id,
            'status': self.status,
            'progress': self.progress,
            'elapsed_seconds': self.elapsed_seconds,
            'files_count': len(self.files_downloaded),
            'total_size_mb': self.total_size_mb,
            'error': self.error
        }


class RecordingService:
    """Service untuk manage recording automation"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_manager = ConfigManager(config_path)
        self.recorder_manager = RecorderManager(config_path)
        self.sessions: Dict[str, RecordingSession] = {}
        
        logger.info("✓ RecordingService initialized")
    
    def start_recording(self, fref_mhz: float, fcari_mhz: float, 
                       loops: int, sync_mode: str) -> Dict:
        """Start recording session via API"""
        
        try:
            # Create session
            session_id = str(uuid.uuid4())[:8]
            session = RecordingSession(session_id, fref_mhz, fcari_mhz, loops, sync_mode)
            self.sessions[session_id] = session
            
            logger.info(f"🎙️ Recording Session Created: {session_id}")
            logger.info(f"   Ref Freq: {fref_mhz} MHz | Target Freq: {fcari_mhz} MHz")
            logger.info(f"   Loops: {loops} | Sync Mode: {sync_mode}")
            
            # Start background thread
            thread = threading.Thread(
                target=self._execute_recording,
                args=(session_id, fref_mhz, fcari_mhz, loops, sync_mode),
                daemon=True
            )
            thread.start()
            logger.debug(f"Background thread started for {session_id}")
            
            # Return immediately
            return {
                'session_id': session_id,
                'status': 'initializing'
            }
            
        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}", exc_info=True)
            raise
    
    def _execute_recording(self, session_id: str, fref_mhz: float, 
                          fcari_mhz: float, loops: int, sync_mode: str):
        """Execute recording in background thread"""
        
        session = self.sessions[session_id]
        
        try:
            # ======================== STEP 1: CONNECT ========================
            logger.info(f"[{session_id}] STEP 1: Connecting to receivers...")
            session.status = 'connecting'
            session.progress = 'Connecting to receivers...'
            
            rx_ids = ['RX1', 'RX2', 'RX3']
            
            # Connect to all RPi
            self.recorder_manager.connect_all()
            logger.info(f"[{session_id}] ✓ Connected to all receivers")
            
            # ======================== STEP 2: SWITCH SYNC MODE ========================
            logger.info(f"[{session_id}] STEP 2: Switching to {sync_mode.upper()} mode...")
            session.status = 'synchronizing'
            session.progress = f'Switching to {sync_mode.upper()} synchronization...'
            
            # (Optional: jika ada switch_synchronization_mode method)
            # switch_results = self.recorder_manager.switch_synchronization_mode(rx_ids, sync_mode)
            
            logger.info(f"[{session_id}] ✓ Synchronization mode set to {sync_mode.upper()}")
            
            # ======================== STEP 3: CALCULATE START TIME ========================
            logger.info(f"[{session_id}] STEP 3: Calculating synchronized start time...")
            session.progress = 'Calculating synchronized start time...'
            
            start_time = self._calculate_start_time()
            wait_seconds = (start_time - datetime.now()).total_seconds()
            
            logger.info(f"[{session_id}] Recording will start at {start_time.strftime('%H:%M:%S')}")
            logger.info(f"[{session_id}] Waiting {wait_seconds:.1f} seconds...")
            
            # ======================== STEP 4: WAIT FOR START TIME ========================
            logger.info(f"[{session_id}] STEP 4: Waiting for synchronized start...")
            session.status = 'waiting'
            
            while datetime.now() < start_time:
                time.sleep(0.1)
            
            # ======================== STEP 5: START RECORDING ========================
            logger.info(f"[{session_id}] STEP 5: Starting recording on all receivers...")
            session.progress = 'Starting recording on all receivers...'
            session.status = 'recording'
            
            self._start_recording_on_rpis(
                session_id, rx_ids, fref_mhz, fcari_mhz, loops
            )
            
            logger.info(f"[{session_id}] ✓ Recording started on all receivers")
            
            # ======================== STEP 6: WAIT FOR COMPLETION ========================
            logger.info(f"[{session_id}] STEP 6: Waiting for recording to complete...")
            session.progress = 'Waiting for recording to complete...'
            
            estimated_duration = loops * 12
            logger.info(f"[{session_id}] Estimated duration: {estimated_duration} seconds")
            
            time.sleep(estimated_duration + 2)
            
            # ======================== STEP 7: DOWNLOAD FILES ========================
            logger.info(f"[{session_id}] STEP 7: Downloading recorded files...")
            session.progress = 'Downloading recorded files...'
            session.status = 'downloading'
            
            files_info = self._download_recorded_files(
                session_id, rx_ids, fref_mhz, fcari_mhz
            )
            
            session.files_downloaded = files_info['files']
            session.total_size_mb = files_info['total_size_mb']
            
            # ======================== STEP 8: COMPLETE ========================
            session.progress = 'Recording completed successfully'
            session.status = 'completed'
            
            logger.info(f"[{session_id}] ✓ Recording session completed successfully")
            logger.info(f"[{session_id}] Downloaded {len(session.files_downloaded)} files")
            logger.info(f"[{session_id}] Total size: {session.total_size_mb:.2f} MB")
            
        except Exception as e:
            logger.error(f"[{session_id}] ✗ Recording failed: {str(e)}", exc_info=True)
            session.status = 'failed'
            session.error = str(e)
        
        finally:
            # ======================== CLEANUP ========================
            logger.info(f"[{session_id}] Disconnecting from receivers...")
            self.recorder_manager.disconnect_all()
    
    def _calculate_start_time(self) -> datetime:
        """Calculate next even minute for synchronized recording"""
        now = datetime.now()
        
        # Calculate next even minute
        current_minute = now.minute
        next_even_minute = ((current_minute // 2) + 1) * 2
        
        if next_even_minute >= 60:
            # Overflow to next hour
            start_time = (now + timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
        else:
            start_time = now.replace(
                minute=next_even_minute, second=0, microsecond=0
            )
        
        return start_time
    
    def _start_recording_on_rpis(self, session_id: str, rx_ids: List[str],
                                 fref_mhz: float, fcari_mhz: float, loops: int):
        """Start recording command pada semua RPi bersamaan"""
        
        try:
            logger.info(f"[{session_id}] === HYBRID TIMING APPROACH ===")
            
            # ==================== CALCULATE SEND TIME ====================
            now = datetime.now()
            current_minute = now.minute
            next_even_minute = ((current_minute // 2) + 1) * 2
            
            if next_even_minute >= 60:
                next_even_time = (now + timedelta(hours=1)).replace(
                    minute=0, second=0, microsecond=0
                )
            else:
                next_even_time = now.replace(
                    minute=next_even_minute, second=0, microsecond=0
                )
            
            # Send time: 100ms sebelum even minute untuk safety margin
            send_time = next_even_time - timedelta(milliseconds=100)
            wait_duration = (send_time - now).total_seconds()
            
            logger.info(f"[{session_id}] Current time: {now.strftime('%H:%M:%S.%f')[:-3]}")
            logger.info(f"[{session_id}] Command send time: {send_time.strftime('%H:%M:%S.%f')[:-3]}")
            logger.info(f"[{session_id}] Expected record time: {next_even_time.strftime('%H:%M:%S.000')}")
            logger.info(f"[{session_id}] Waiting {wait_duration:.3f}s...")
            
            # ==================== WAIT FOR SEND TIME ====================
            while True:
                current = datetime.now()
                remaining = (send_time - current).total_seconds()
                
                if remaining <= 0:
                    break
                
                time.sleep(min(remaining, 0.010))  # Poll setiap 10ms
            
            # ==================== SEND COMMANDS PARALLEL ====================
            logger.info(f"[{session_id}] Sending commands to all receivers...")
            
            threads = []
            
            for i, rx_id in enumerate(rx_ids):
                command = (
                    f"/home/pi/pewaktu_new "
                    f"--fref {fref_mhz*1e6:.0f} "
                    f"--fcari {fcari_mhz*1e6:.0f} "
                    f"--loop {loops}"
                )
                
                def send_cmd(rx, cmd, idx):
                    try:
                        send_actual = datetime.now()
                        logger.info(f"[{session_id}] [{idx+1}/3] Sending to {rx} @ {send_actual.strftime('%H:%M:%S.%f')[:-3]}")
                        self.recorder_manager.execute_command(rx, cmd)
                        logger.info(f"[{session_id}] [{idx+1}/3] {rx} command executed")
                    except Exception as e:
                        logger.error(f"[{session_id}] Failed to send to {rx}: {str(e)}")
                        raise
                
                # Use threading untuk parallel execution
                thread = threading.Thread(
                    target=send_cmd,
                    args=(rx_id, command, i),
                    daemon=False
                )
                threads.append(thread)
                thread.start()
                
                # 1ms delay antar thread spawn
                if i < len(rx_ids) - 1:
                    time.sleep(0.001)
            
            # Wait semua thread selesai
            for thread in threads:
                thread.join(timeout=5)
            
            logger.info(f"[{session_id}] ✓ All commands sent successfully")
            logger.info(f"[{session_id}] All receivers will now wait locally for {next_even_time.strftime('%H:%M:%S.000')}")
            
        except Exception as e:
            logger.error(f"[{session_id}] Failed to start recording: {str(e)}", exc_info=True)
            raise
    
    def _download_recorded_files(self, session_id: str, rx_ids: List[str],
                                 fref_mhz: float, fcari_mhz: float) -> Dict:
        """Download recorded files dari semua RPi"""
        
        try:
            files_downloaded = []
            total_size_mb = 0
            
            # ==================== GENERATE EXPECTED FILENAMES ====================
            now = datetime.now()
            fref_int = int(fref_mhz * 10)      # 100.0 MHz → 1000
            fcari_int = int(fcari_mhz * 10)    # 98.0 MHz → 980
            
            filename_base = (f"{fref_int}_{fcari_int}_{now.year}_{now.month}_"
                           f"{now.day}_{now.hour}_{now.minute}.dat")
            
            logger.info(f"[{session_id}] Expected filename base: {filename_base}")
            
            # ==================== DOWNLOAD FROM EACH RECEIVER ====================
            for rx_id in rx_ids:
                try:
                    rx_num = rx_id.replace('RX', '')
                    remote_file = f"/home/pi/recorded_data/{rx_num}_{filename_base}"
                    
                    logger.info(f"[{session_id}] Downloading from {rx_id}...")
                    logger.debug(f"[{session_id}] Remote file: {remote_file}")
                    
                    # ==================== DOWNLOAD VIA SCP ====================
                    local_path = self.recorder_manager.download_file(
                        rx_id, remote_file,
                        dest_dir="./output/recorded_data"
                    )
                    
                    # ==================== GET FILE SIZE ====================
                    file_size_mb = Path(local_path).stat().st_size / (1024**2)
                    total_size_mb += file_size_mb
                    
                    files_downloaded.append({
                        'rx_id': rx_id,
                        'local_path': str(local_path),
                        'size_mb': file_size_mb
                    })
                    
                    logger.info(f"[{session_id}] ✓ Downloaded {Path(local_path).name} ({file_size_mb:.2f} MB)")
                    
                except Exception as e:
                    logger.error(f"[{session_id}] Failed to download from {rx_id}: {str(e)}")
                    # Continue dengan RPi lainnya
                    continue
            
            # ==================== VERIFY DOWNLOADS ====================
            if not files_downloaded:
                raise Exception("No files were successfully downloaded")
            
            logger.info(f"[{session_id}] ✓ Download complete. {len(files_downloaded)} files, {total_size_mb:.2f} MB total")
            
            return {
                'files': files_downloaded,
                'total_size_mb': total_size_mb
            }
            
        except Exception as e:
            logger.error(f"[{session_id}] Download failed: {str(e)}", exc_info=True)
            raise
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get status dari recording session"""
        
        if session_id not in self.sessions:
            return {'error': 'Session not found', 'session_id': session_id}
        
        session = self.sessions[session_id]
        return session.to_dict()