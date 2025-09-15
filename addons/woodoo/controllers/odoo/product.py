import logging
from odoo import models, api


# Set up dedicated file logger
def get_product_logger():
    """Get or create a dedicated logger for product title changes"""
    logger_name = 'wooodoo_product_title_logger'
    logger = logging.getLogger(logger_name)

    # Only set up if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create file handler
        try:
            file_handler = logging.FileHandler('/tmp/woodoo.log', mode='a')
            file_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.propagate = False  # Prevent propagation to root logger
        except (IOError, OSError) as e:
            # If file cannot be created/accessed, log to standard logger
            standard_logger = logging.getLogger(__name__)
            standard_logger.warning(
                f"Cannot write to /tmp/woodoo.log: {e}. Product changes will be logged to standard log.")
            return standard_logger

    return logger


class Product(models.Model):
    # check if user edit product title
    def product_title_changed(self, product, new_title):
        if product.name != new_title:
            # write to /tmp/odoo.log
            return True
        return False


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        """Override write method to log product template title changes"""

        # Check if 'name' field is being updated
        if 'name' in vals:
            logger = get_product_logger()

            for record in self:
                old_name = record.name or ''  # Handle None values
                new_name = vals['name'] or ''

                # Only log if the name actually changed
                if old_name != new_name:
                    user_name = self.env.user.name if self.env.user else 'System'
                    user_id = self.env.user.id if self.env.user else 'N/A'

                    log_message = (
                        f"Product Template ID: {record.id} | "
                        f"User: {user_name} (ID: {user_id}) | "
                        f"Old Title: '{old_name}' | "
                        f"New Title: '{new_name}'"
                    )

                    try:
                        logger.info(log_message)
                    except Exception as e:
                        # Fallback logging if file logging fails
                        fallback_logger = logging.getLogger(__name__)
                        fallback_logger.error(f"Failed to log to file: {e}")
                        fallback_logger.info(f"Product template title change: {log_message}")

        # Call the original write method
        return super(ProductTemplate, self).write(vals)
