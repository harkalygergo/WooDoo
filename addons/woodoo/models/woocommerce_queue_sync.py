from odoo import models, api, fields
from odoo.addons.queue_job.job import job
import logging
import os
import subprocess
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WooCommerceSyncQueue(models.Model):
    _name = 'woocommerce.sync.queue'
    _description = 'WooCommerce Queue Synchronization'

    name = fields.Char('Sync Name', default='WooCommerce Queue Sync', required=True)
    last_sync = fields.Datetime('Last Sync')
    sync_count = fields.Integer('Sync Count', default=0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('error', 'Error')
    ], default='draft')

    @api.model
    def sync_woocommerce_orders_cron(self):
        """Cron job method that creates a queue job"""
        try:
            # Check if there's already a running sync
            running_sync = self.search([('state', '=', 'running')], limit=1)
            if running_sync:
                _logger.info("WooCommerce sync already running, skipping...")
                return

            # Create a queue job
            self.with_delay(priority=5, max_retries=3).sync_woocommerce_orders()
            _logger.info("WooCommerce sync job queued successfully")

        except Exception as e:
            _logger.error(f"Error queuing WooCommerce sync: {str(e)}")

    @job(default_channel='root.woocommerce')
    def sync_woocommerce_orders(self):
        """Actual sync method running as queue job"""
        sync_record = None
        try:
            _logger.info("=== Starting WooCommerce Orders Sync (Queue Job) ===")

            # Create or get sync record
            sync_record = self.search([], limit=1)
            if not sync_record:
                sync_record = self.create({
                    'name': 'WooCommerce Queue Sync',
                    'state': 'running'
                })
            else:
                sync_record.state = 'running'

            # Execute the sync
            self._execute_external_script()

            # Update sync record
            sync_record.write({
                'last_sync': fields.Datetime.now(),
                'sync_count': sync_record.sync_count + 1,
                'state': 'done'
            })

            _logger.info("=== WooCommerce Orders Sync Completed Successfully ===")

        except Exception as e:
            if sync_record:
                sync_record.state = 'error'
            _logger.error(f"=== WooCommerce Sync Failed: {str(e)} ===")
            raise

    def _execute_external_script(self):
        """Execute the external Python script with improved error handling"""
        try:
            # Get the module path
            import woodoo  # Your module name
            module_path = os.path.dirname(woodoo.__file__)

            # Try different possible locations for the script
            possible_paths = [
                os.path.join(module_path, 'dev', 'get-woocommerce-orders.py'),
                os.path.join(module_path, 'models', 'get-woocommerce-orders.py'),
                os.path.join(module_path, 'scripts', 'get-woocommerce-orders.py'),
            ]

            script_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    script_path = path
                    break

            if not script_path:
                raise UserError(f"Script not found in any of these locations: {possible_paths}")

            _logger.info(f"Found script at: {script_path}")

            # Set up environment variables
            env = os.environ.copy()
            env.update({
                'PYTHONPATH': f"{module_path}:{env.get('PYTHONPATH', '')}",
                'ODOO_DATABASE': self.env.cr.dbname,
                'ODOO_DB_HOST': self.env.cr._cnx.info.host or 'localhost',
                'ODOO_DB_PORT': str(self.env.cr._cnx.info.port or 5432),
            })

            # Execute the script
            _logger.info("Executing WooCommerce script...")
            result = subprocess.run([
                'python3', script_path
            ],
                capture_output=True,
                text=True,
                cwd=module_path,
                env=env,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                _logger.info("Script executed successfully")
                if result.stdout:
                    _logger.info(f"Script output: {result.stdout[:1000]}...")
            else:
                error_msg = f"Script failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nError: {result.stderr[:1000]}..."
                if result.stdout:
                    error_msg += f"\nOutput: {result.stdout[:1000]}..."
                _logger.error(error_msg)
                raise UserError(error_msg)

        except subprocess.TimeoutExpired:
            error_msg = "Script execution timed out (10 minutes)"
            _logger.error(error_msg)
            raise UserError(error_msg)
        except Exception as e:
            _logger.error(f"Error executing script: {str(e)}")
            raise

    @api.model
    def manual_sync(self):
        """Manual sync method for testing"""
        return self.sync_woocommerce_orders()
