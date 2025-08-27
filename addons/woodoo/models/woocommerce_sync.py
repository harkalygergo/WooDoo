from odoo import models, api, fields
import logging
import os
import subprocess
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_logger.info("=== Starting WooDoo ===")


class WooCommerceSync(models.Model):
    _name = 'woocommerce.sync'
    _description = 'WooCommerce Synchronization'

    name = fields.Char('Sync Name', default='WooCommerce Sync', required=True)
    last_sync = fields.Datetime('Last Sync')
    sync_count = fields.Integer('Sync Count', default=0)

    @api.model
    def sync_woocommerce_orders(self):
        """Method to be called by cron job with proper connection management"""
        _logger.info("=== Starting WooCommerce Orders Sync ===")

        # Use a separate database cursor to avoid connection issues
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                try:
                    # Create new environment with fresh cursor
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    sync_obj = new_env['woocommerce.sync']

                    # Execute the sync with new environment
                    sync_obj._execute_external_script()
                    sync_obj._update_sync_record()

                    # Commit the transaction
                    new_cr.commit()
                    _logger.info("=== WooCommerce Orders Sync Completed Successfully ===")

                except Exception as e:
                    # Rollback on error
                    new_cr.rollback()
                    _logger.error(f"=== WooCommerce Sync Failed: {str(e)} ===")
                    # Don't re-raise to prevent cron job from failing repeatedly

    def _execute_external_script(self):
        """Execute the external Python script"""
        try:
            # Get the module path
            module_path = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(module_path, 'dev', 'get-woocommerce-orders.py')

            _logger.info(f"Module path: {module_path}")
            _logger.info(f"Script path: {script_path}")

            if not os.path.exists(script_path):
                # Try alternative path
                script_path = os.path.join(module_path, 'models', 'get-woocommerce-orders.py')
                _logger.info(f"Alternative script path: {script_path}")

            if not os.path.exists(script_path):
                raise UserError(f"Script not found at: {script_path}")

            # Set up environment variables
            env = os.environ.copy()
            env.update({
                'PYTHONPATH': module_path,
                'ODOO_DATABASE': self.env.cr.dbname,
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
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                _logger.info("Script executed successfully")
                if result.stdout:
                    _logger.info(f"Script output: {result.stdout[:500]}...")  # Limit log size
            else:
                error_msg = f"Script failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nError: {result.stderr}"
                _logger.error(error_msg)
                raise UserError(error_msg)

        except subprocess.TimeoutExpired:
            error_msg = "Script execution timed out (5 minutes)"
            _logger.error(error_msg)
            raise UserError(error_msg)
        except Exception as e:
            _logger.error(f"Error executing script: {str(e)}")
            raise

    def _update_sync_record(self):
        """Update or create sync record"""
        try:
            sync_record = self.search([], limit=1)
            if not sync_record:
                sync_record = self.create({
                    'name': 'WooCommerce Orders Sync',
                    'last_sync': fields.Datetime.now(),
                    'sync_count': 1
                })
            else:
                sync_record.write({
                    'last_sync': fields.Datetime.now(),
                    'sync_count': sync_record.sync_count + 1
                })

            _logger.info(f"Updated sync record. Total syncs: {sync_record.sync_count}")
        except Exception as e:
            _logger.error(f"Error updating sync record: {str(e)}")

    @api.model
    def manual_sync(self):
        """Manual sync method for testing"""
        return self.sync_woocommerce_orders()
