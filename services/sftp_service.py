"""
SFTP Service for uploading MT940 files to remote servers
"""
import os
import paramiko
from datetime import datetime
from flask import current_app


class SFTPService:
    """Service to handle SFTP file uploads"""

    @staticmethod
    def upload_file(local_file_path, company, original_filename=None):
        """
        Upload file to SFTP server using company's SFTP configuration

        Args:
            local_file_path: Path to local file to upload
            company: Company object with SFTP credentials
            original_filename: Original filename (optional, will use local filename if not provided)

        Returns:
            dict: {"success": bool, "message": str, "remote_path": str or None}
        """

        # Validate SFTP configuration
        if not company.sftp_host:
            return {
                "success": False,
                "message": "SFTP host không được cấu hình",
                "remote_path": None
            }

        if not company.sftp_username:
            return {
                "success": False,
                "message": "SFTP username không được cấu hình",
                "remote_path": None
            }

        # Check if file exists
        if not os.path.exists(local_file_path):
            return {
                "success": False,
                "message": f"File không tồn tại: {local_file_path}",
                "remote_path": None
            }

        # Prepare remote filename with timestamp and .txt extension for MT940
        if original_filename:
            # Remove any path separators from original filename
            base_name = os.path.basename(original_filename)
            base_name, ext = os.path.splitext(base_name)
        else:
            base_name, ext = os.path.splitext(os.path.basename(local_file_path))

        # Always use .txt extension for MT940 files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_filename = f"{base_name}_{timestamp}.txt"

        # Determine remote path - upload directly to /in folder
        remote_path = company.sftp_remote_path or "/in"
        # Ensure path ends with /
        if not remote_path.endswith("/"):
            remote_path += "/"
        remote_file_path = f"{remote_path}{remote_filename}"

        # Initialize SFTP connection
        ssh = None
        sftp = None

        try:
            current_app.logger.info(f"Connecting to SFTP: {company.sftp_host}:{company.sftp_port}")

            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with password or key
            connect_kwargs = {
                'hostname': company.sftp_host,
                'port': company.sftp_port or 22,
                'username': company.sftp_username,
                'timeout': 60
            }

            if company.sftp_private_key_path and os.path.exists(company.sftp_private_key_path):
                # Use private key authentication
                current_app.logger.info(f"Using private key: {company.sftp_private_key_path}")
                connect_kwargs['key_filename'] = company.sftp_private_key_path
            elif company.sftp_password:
                # Use password authentication
                current_app.logger.info("Using password authentication")
                connect_kwargs['password'] = company.sftp_password
            else:
                return {
                    "success": False,
                    "message": "Không có mật khẩu hoặc private key để xác thực",
                    "remote_path": None
                }

            ssh.connect(**connect_kwargs)

            # Open SFTP session
            sftp = ssh.open_sftp()
            current_app.logger.info(f"SFTP connection established")

            # Verify remote directory exists (do not create, just check)
            try:
                sftp.stat(remote_path.rstrip('/'))
                current_app.logger.info(f"Remote directory exists: {remote_path}")
            except FileNotFoundError:
                return {
                    "success": False,
                    "message": f"Thư mục remote không tồn tại: {remote_path}. Vui lòng tạo thư mục trên server SFTP.",
                    "remote_path": None
                }

            # Upload file directly to /in folder
            current_app.logger.info(f"Uploading {local_file_path} to {remote_file_path}")
            sftp.put(local_file_path, remote_file_path)

            # Verify upload
            remote_stat = sftp.stat(remote_file_path)
            local_size = os.path.getsize(local_file_path)

            if remote_stat.st_size == local_size:
                current_app.logger.info(f"Upload successful: {remote_file_path} ({local_size} bytes)")
                return {
                    "success": True,
                    "message": f"Upload thành công: {remote_filename}",
                    "remote_path": remote_file_path
                }
            else:
                return {
                    "success": False,
                    "message": f"Kích thước file không khớp (local: {local_size}, remote: {remote_stat.st_size})",
                    "remote_path": None
                }

        except paramiko.AuthenticationException as e:
            current_app.logger.error(f"SFTP authentication failed: {e}")
            return {
                "success": False,
                "message": f"Xác thực SFTP thất bại: {str(e)}",
                "remote_path": None
            }
        except paramiko.SSHException as e:
            current_app.logger.error(f"SFTP SSH error: {e}")
            return {
                "success": False,
                "message": f"Lỗi SSH: {str(e)}",
                "remote_path": None
            }
        except FileNotFoundError as e:
            current_app.logger.error(f"File not found: {e}")
            return {
                "success": False,
                "message": f"Không tìm thấy file: {str(e)}",
                "remote_path": None
            }
        except Exception as e:
            current_app.logger.error(f"SFTP upload error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Lỗi upload: {str(e)}",
                "remote_path": None
            }
        finally:
            # Close connections
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()
            current_app.logger.info("SFTP connection closed")
