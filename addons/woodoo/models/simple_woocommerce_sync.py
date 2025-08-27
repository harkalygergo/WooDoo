from odoo import models, api, fields
import logging
import os
import subprocess
import threading
import time

_logger = logging.getLogger(__name__)


class SimpleWooCommerceSync(models.Model):
    _name = 'simple.woocommerce.sync'
    _description = 'Simple WooCommerce Synchronization'

    name = fields.Char('Sync Name', default='Simple WooCommerce Sync')
    last_sync = fields.Datetime('Last Sync')
    is_running = fields.Boolean('Is Running', default=False)

    @api.model
    def sync_woocommerce_orders(self):
        """Simple cron method with basic locking"""

        # Check if sync is already running
        running_record = self.search([('is_running', '=', True)], limit=1)
        if running_record:
            _logger.info("WooCommerce sync already running, skipping...")
            return

        # Create or get sync record
        sync_record = self.search([], limit=1)
        if not sync_record:
            sync_record = self.create({'name': 'Simple WooCommerce Sync'})

        try:
            # Mark as running
            sync_record.is_running = True
            self.env.cr.commit()

            _logger.info("=== Starting Simple WooCommerce Orders Sync ===")

            # Execute sync in a separate thread to avoid blocking
            thread = threading.Thread(target=self._run_sync_thread, args=(sync_record.id,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            sync_record.is_running = False
            self.env.cr.commit()
            _logger.error(f"Error starting WooCommerce sync: {str(e)}")

    def _run_sync_thread(self, sync_record_id):
        """Run sync in separate thread"""
        try:
            time.sleep(1)  # Small delay to ensure main transaction is committed

            # Create new database connection for the thread
            with self.pool.cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, {})
                sync_record = new_env['simple.woocommerce.sync'].browse(sync_record_id)

                try:
                    # Execute the external script
                    self._execute_script_simple(new_env)

                    # Update record
                    sync_record.write({
                        'last_sync': fields.Datetime.now(),
                        'is_running': False
                    })
                    new_cr.commit()

                    _logger.info("=== Simple WooCommerce Sync Completed ===")

                except Exception as e:
                    sync_record.is_running = False
                    new_cr.commit()
                    _logger.error(f"Error in sync thread: {str(e)}")

        except Exception as e:
            _logger.error(f"Critical error in sync thread: {str(e)}")

    def _execute_script_simple(self, env):
        """Execute the script with minimal setup"""
        try:
            # Find the script
            module_dir = os.path.dirname(os.path.dirname(__file__))
            script_paths = [
                os.path.join(module_dir, 'dev', 'get-woocommerce-orders.py'),
                os.path.join(module_dir, 'models', 'get-woocommerce-orders.py'),
            ]

            script_path = None
            for path in script_paths:
                if os.path.exists(path):
                    script_path = path
                    break

            if not script_path:
                _logger.error(f"Script not found in: {script_paths}")
                return

            _logger.info(f"Executing script: {script_path}")

            # Simple execution
            result = subprocess.run([
                'python3', script_path
            ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                cwd=module_dir
            )

            if result.returncode == 0:
                _logger.info("Script completed successfully")
            else:
                _logger.error(f"Script failed: {result.stderr}")

        except Exception as e:
            _logger.error(f"Script execution error: {str(e)}")

    @api.model
    def reset_running_flag(self):
        """Reset running flag if stuck"""
        stuck_records = self.search([('is_running', '=', True)])
        if stuck_records:
            stuck_records.is_running = False
            _logger.info(f"Reset {len(stuck_records)} stuck sync records")
