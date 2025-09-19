from odoo import models, api
import logging
import json
import os
from datetime import datetime

from addons.woodoo.controllers.logger import Logger
from addons.woodoo.controllers.woo.api import WooAPI

# Set up custom logger for invoice data
invoice_logger = logging.getLogger('invoice_data')
invoice_handler = logging.FileHandler('/tmp/odoo.log')
invoice_formatter = logging.Formatter(
    '%(asctime)s - INVOICE_LOG - %(levelname)s - %(message)s'
)
invoice_handler.setFormatter(invoice_formatter)
invoice_logger.addHandler(invoice_handler)
invoice_logger.setLevel(logging.INFO)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to log invoice data - supports batch creation"""
        # Handle single dict input (convert to list)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        # Create the invoices first
        invoices = super(AccountMoveInherit, self).create(vals_list)

        # Log each invoice that's actually an invoice (not journal entries, etc.)
        for invoice in invoices:
            if invoice.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                self._log_invoice_data(invoice)

        return invoices

    def write(self, vals):
        """Override write method to log when invoice is validated/posted"""
        result = super(AccountMoveInherit, self).write(vals)

        # Log when state changes to posted (validated)
        if 'state' in vals and vals['state'] == 'posted':
            for invoice in self:
                if invoice.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                    self._log_invoice_validation(invoice)
                    self._sync_invoice_to_woocommerce(invoice)
                    """
                    try:
                        wooAPI = WooAPI.get(self)
                        data = {
                            "id": self.id,
                            "status": "completed" if vals['payment_state'] == 'paid' else "pending",
                        }
                        Logger.log(f"Syncing Invoice to WooCommerce: {data}")
                        response = wooAPI.put(f"orders/{self.id}", data)
                        if response.status_code != 200:
                            Logger.log(f"API error while syncing Invoice: {response.status_code} {response.text}")
                        else:
                            Logger.log(f"Successfully synced Invoice to WooCommerce: {response.json()}")
                    except Exception as e:
                        Logger.log(f"Error while syncing Invoice to WooCommerce: {e}")
                    """

        return result

    def _sync_invoice_to_woocommerce(self, invoice):
        """Sync invoice data to WooCommerce when validated"""
        try:
            # Skip if not a customer invoice or refund
            if invoice.move_type not in ['out_invoice', 'out_refund']:
                return

            # Get WooCommerce order ID from invoice origin or reference
            woo_order_id = self._get_woocommerce_order_id(invoice)
            if not woo_order_id:
                invoice_logger.warning(f"No WooCommerce order ID found for invoice {invoice.name}")
                return

            # Prepare invoice data for WooCommerce
            invoice_data = self._prepare_woocommerce_invoice_data(invoice)

            # Create note content for WordPress order
            note_content = self._create_invoice_note_content(invoice, invoice_data)

            # Send invoice data to WooCommerce order notes
            woo_note_data = {
                "note": note_content,
                "customer_note": False,  # Internal note
                "added_by_user": True
            }

            # Add note to WooCommerce order using the live API
            try:
                wooAPI = WooAPI.get(self)
                # Add note to order
                response = wooAPI.post(f"orders/{woo_order_id}/notes", woo_note_data)

                if response.status_code == 201:
                    invoice_logger.info(f"Successfully added invoice note to WooCommerce order {woo_order_id}")

                    # Optional: Update order meta with invoice info
                    order_meta_data = {
                        "meta_data": [
                            {
                                "key": f"_odoo_invoice_{invoice.id}",
                                "value": {
                                    "invoice_number": invoice.name,
                                    "invoice_date": invoice.invoice_date.strftime(
                                        '%Y-%m-%d') if invoice.invoice_date else None,
                                    "amount_total": float(invoice.amount_total),
                                    "currency": invoice.currency_id.name if invoice.currency_id else None,
                                    "state": invoice.state
                                }
                            }
                        ]
                    }

                    # Update order with invoice metadata
                    meta_response = wooAPI.put(f"orders/{woo_order_id}", order_meta_data)

                    if meta_response.status_code == 200:
                        invoice_logger.info(
                            f"Successfully updated WooCommerce order {woo_order_id} with invoice metadata")
                    else:
                        invoice_logger.warning(f"Failed to update order metadata: {meta_response.text}")

                else:
                    invoice_logger.error(f"Failed to add note to WooCommerce order {woo_order_id}: {response.text}")

            except Exception as api_error:
                invoice_logger.error(f"WooCommerce API error for invoice {invoice.name}: {str(api_error)}")

        except Exception as e:
            invoice_logger.error(f"Error syncing invoice {invoice.name} to WooCommerce: {str(e)}")

    def _log_invoice_data(self, invoice):
        """Log detailed invoice data to file"""
        try:
            # Use sudo() to avoid permission issues when logging
            invoice = invoice.sudo()

            # Prepare invoice data dictionary
            invoice_data = {
                'action': 'INVOICE_CREATED',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'invoice_id': invoice.id,
                'invoice_number': invoice.name or 'Draft',
                'invoice_type': invoice.move_type,
                'state': invoice.state,
                'partner_info': {
                    'partner_id': invoice.partner_id.id if invoice.partner_id else None,
                    'partner_name': invoice.partner_id.name if invoice.partner_id else 'No Partner',
                    'partner_email': invoice.partner_id.email if invoice.partner_id else None,
                    'partner_vat': invoice.partner_id.vat if invoice.partner_id else None,
                },
                'financial_info': {
                    'currency': invoice.currency_id.name if invoice.currency_id else None,
                    'amount_untaxed': float(invoice.amount_untaxed) if invoice.amount_untaxed else 0.0,
                    'amount_tax': float(invoice.amount_tax) if invoice.amount_tax else 0.0,
                    'amount_total': float(invoice.amount_total) if invoice.amount_total else 0.0,
                    'amount_residual': float(invoice.amount_residual) if invoice.amount_residual else 0.0,
                },
                'dates': {
                    'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else None,
                    'invoice_date_due': invoice.invoice_date_due.strftime(
                        '%Y-%m-%d') if invoice.invoice_date_due else None,
                    'create_date': invoice.create_date.strftime('%Y-%m-%d %H:%M:%S') if invoice.create_date else None,
                },
                'company_info': {
                    'company_id': invoice.company_id.id if invoice.company_id else None,
                    'company_name': invoice.company_id.name if invoice.company_id else None,
                },
                'invoice_lines': [],
                'payment_terms': invoice.invoice_payment_term_id.name if invoice.invoice_payment_term_id else None,
                'invoice_origin': invoice.invoice_origin or None,
                'reference': invoice.ref or None,
                'narration': invoice.narration or None,
            }

            # Add invoice line details
            for line in invoice.invoice_line_ids:
                line_data = {
                    'line_id': line.id,
                    'product_id': line.product_id.id if line.product_id else None,
                    'product_name': line.product_id.name if line.product_id else None,
                    'product_code': line.product_id.default_code if line.product_id else None,
                    'description': line.name or '',
                    'quantity': float(line.quantity) if line.quantity else 0.0,
                    'price_unit': float(line.price_unit) if line.price_unit else 0.0,
                    'price_subtotal': float(line.price_subtotal) if line.price_subtotal else 0.0,
                    'price_total': float(line.price_total) if line.price_total else 0.0,
                    'account_id': line.account_id.id if line.account_id else None,
                    'account_code': line.account_id.code if line.account_id else None,
                    'tax_ids': [tax.name for tax in line.tax_ids] if line.tax_ids else [],
                }
                invoice_data['invoice_lines'].append(line_data)

            # Log the data
            log_message = f"NEW INVOICE DATA: {json.dumps(invoice_data, indent=2, default=str)}"
            invoice_logger.info(log_message)

            # Also log a summary line for easy reading
            summary = (f"Invoice Created - ID: {invoice.id}, "
                       f"Partner: {invoice.partner_id.name if invoice.partner_id else 'None'}, "
                       f"Amount: {invoice.amount_total} {invoice.currency_id.name if invoice.currency_id else ''}, "
                       f"Type: {invoice.move_type}")
            invoice_logger.info(f"SUMMARY: {summary}")

        except Exception as e:
            invoice_logger.error(
                f"Error logging invoice data for ID {invoice.id if hasattr(invoice, 'id') else 'Unknown'}: {str(e)}")

    def _log_invoice_validation(self, invoice):
        """Log when invoice gets validated/posted"""
        try:
            validation_data = {
                'action': 'INVOICE_VALIDATED',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'invoice_id': invoice.id,
                'invoice_number': invoice.name,
                'partner_name': invoice.partner_id.name if invoice.partner_id else 'No Partner',
                'amount_total': float(invoice.amount_total),
                'currency': invoice.currency_id.name if invoice.currency_id else None,
                'validation_date': invoice.write_date.strftime('%Y-%m-%d %H:%M:%S') if invoice.write_date else None,
            }

            log_message = f"INVOICE VALIDATED: {json.dumps(validation_data, indent=2)}"
            invoice_logger.info(log_message)

        except Exception as e:
            invoice_logger.error(f"Error logging invoice validation for ID {invoice.id}: {str(e)}")

    def _get_woocommerce_order_id(self, invoice):
        """Extract WooCommerce order ID from invoice origin or reference"""
        try:
            # Method 1: Check invoice origin (e.g., "WOO-123", "SO001-WOO-456")
            if invoice.invoice_origin:
                # Look for WOO- prefix
                import re
                orderName = invoice.invoice_origin.upper()
                orderName = re.sub(r'\D', '', orderName)
                if orderName.isdigit():
                    return int(orderName)

                # Look for just numbers if origin is pure numeric
                if invoice.invoice_origin.isdigit():
                    return int(invoice.invoice_origin)

            # Method 2: Check reference field
            if invoice.ref:
                woo_match = re.search(r'WOO-(\d+)', invoice.ref.upper())
                if woo_match:
                    return int(woo_match.group(1))

                if invoice.ref.isdigit():
                    return int(invoice.ref)

            # Method 3: Check if there's a related sale order with WooCommerce info
            if hasattr(invoice, 'invoice_line_ids'):
                for line in invoice.invoice_line_ids:
                    if line.sale_line_ids:
                        for sale_line in line.sale_line_ids:
                            if sale_line.order_id and sale_line.order_id.client_order_ref:
                                ref = sale_line.order_id.client_order_ref
                                if ref and 'WOO' in ref.upper():
                                    woo_match = re.search(r'WOO-?(\d+)', ref.upper())
                                    if woo_match:
                                        return int(woo_match.group(1))

            return None

        except Exception as e:
            invoice_logger.error(f"Error extracting WooCommerce order ID from invoice {invoice.name}: {str(e)}")
            return None

    def _prepare_woocommerce_invoice_data(self, invoice):
        """Prepare invoice data for WooCommerce sync"""
        try:
            invoice_data = {
                'invoice_id': invoice.id,
                'invoice_number': invoice.name,
                'invoice_type': invoice.move_type,
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else None,
                'due_date': invoice.invoice_date_due.strftime('%Y-%m-%d') if invoice.invoice_date_due else None,
                'amount_untaxed': float(invoice.amount_untaxed),
                'amount_tax': float(invoice.amount_tax),
                'amount_total': float(invoice.amount_total),
                'currency': invoice.currency_id.name if invoice.currency_id else None,
                'state': invoice.state,
                'partner_name': invoice.partner_id.name if invoice.partner_id else None,
                'company_name': invoice.company_id.name if invoice.company_id else None,
                'payment_term': invoice.invoice_payment_term_id.name if invoice.invoice_payment_term_id else None,
                'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'invoice_lines': []
            }

            # Add simplified line data
            for line in invoice.invoice_line_ids:
                if line.display_type not in ('line_section', 'line_note'):  # Skip section/note lines
                    line_data = {
                        'product_name': line.product_id.name if line.product_id else line.name,
                        'quantity': float(line.quantity),
                        'price_unit': float(line.price_unit),
                        'price_total': float(line.price_total)
                    }
                    invoice_data['invoice_lines'].append(line_data)

            return invoice_data

        except Exception as e:
            invoice_logger.error(f"Error preparing WooCommerce data for invoice {invoice.name}: {str(e)}")
            return {}

    def _create_invoice_note_content(self, invoice, invoice_data):
        """Create formatted note content for WooCommerce order"""
        try:
            invoice_type_display = {
                'out_invoice': 'Customer Invoice',
                'out_refund': 'Customer Refund',
                'in_invoice': 'Vendor Bill',
                'in_refund': 'Vendor Refund'
            }

            # Create main note content
            note_lines = [
                f"📄 **{invoice_type_display.get(invoice.move_type, 'Invoice')} Created in Odoo**",
                f"",
                f"**Invoice Number:** {invoice.name}",
                f"**Invoice Date:** {invoice.invoice_date.strftime('%B %d, %Y') if invoice.invoice_date else 'Not set'}",
            ]

            if invoice.invoice_date_due:
                note_lines.append(f"**Due Date:** {invoice.invoice_date_due.strftime('%B %d, %Y')}")

            note_lines.extend([
                f"**Amount (excl. tax):** {invoice.amount_untaxed:.2f} {invoice.currency_id.name if invoice.currency_id else ''}",
                f"**Tax Amount:** {invoice.amount_tax:.2f} {invoice.currency_id.name if invoice.currency_id else ''}",
                f"**Total Amount:** {invoice.amount_total:.2f} {invoice.currency_id.name if invoice.currency_id else ''}",
                f"**Status:** {invoice.state.title()}",
                f"**Validation Date:** {datetime.now().strftime('%B %d, %Y at %H:%M')}",
                f""
            ])

            # Add payment terms if available
            if invoice.invoice_payment_term_id:
                note_lines.append(f"**Payment Terms:** {invoice.invoice_payment_term_id.name}")

            # Add reference info if available
            if invoice.ref:
                note_lines.append(f"**Reference:** {invoice.ref}")

            # Add line items summary
            if invoice_data.get('invoice_lines'):
                note_lines.extend([
                    f"",
                    f"**Invoice Items:**"
                ])

                for line in invoice_data['invoice_lines'][:5]:  # Limit to 5 items to avoid too long notes
                    note_lines.append(
                        f"• {line['product_name']}: {line['quantity']} × {line['price_unit']:.2f} = {line['price_total']:.2f}")

                if len(invoice_data['invoice_lines']) > 5:
                    note_lines.append(f"• ... and {len(invoice_data['invoice_lines']) - 5} more items")

            # Add footer
            note_lines.extend([
                f"",
                f"---",
                f"Generated automatically from Odoo ERP system",
                f"Invoice ID: {invoice.id}"
            ])

            return "\n".join(note_lines)

        except Exception as e:
            invoice_logger.error(f"Error creating note content for invoice {invoice.name}: {str(e)}")
            return f"Invoice {invoice.name} has been validated in Odoo ERP system.\nTotal: {invoice.amount_total} {invoice.currency_id.name if invoice.currency_id else ''}"

    @api.model
    def _log_system_info(self):
        """Log system information - can be called manually"""
        try:
            system_info = {
                'action': 'SYSTEM_INFO',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'log_file_path': '/tmp/odoo.log',
                'log_file_exists': os.path.exists('/tmp/odoo.log'),
                'log_file_writable': os.access('/tmp', os.W_OK),
                'database': self.env.cr.dbname,
                'company_id': self.env.company.id,
                'company_name': self.env.company.name,
                'user_id': self.env.user.id,
                'user_name': self.env.user.name,
            }

            log_message = f"SYSTEM INFO: {json.dumps(system_info, indent=2)}"
            invoice_logger.info(log_message)

        except Exception as e:
            invoice_logger.error(f"Error logging system info: {str(e)}")


# You can also add a scheduled action to clean up old logs
class InvoiceLoggerCron(models.Model):
    _name = 'invoice.logger.cron'
    _description = 'Invoice Logger Cleanup'

    @api.model
    def cleanup_old_logs(self):
        """Clean up logs older than 30 days - call this via cron"""
        try:
            log_file = '/tmp/odoo.log'
            if os.path.exists(log_file):
                # Get file age
                file_age = datetime.now().timestamp() - os.path.getmtime(log_file)
                days_old = file_age / (24 * 3600)

                if days_old > 30:  # If older than 30 days
                    # Archive old log
                    archive_name = f'/tmp/odoo_archive_{datetime.now().strftime("%Y%m%d")}.log'
                    os.rename(log_file, archive_name)

                    # Log the cleanup
                    invoice_logger.info(f"Log file archived to {archive_name}")

        except Exception as e:
            invoice_logger.error(f"Error during log cleanup: {str(e)}")


# Utility function for manual testing
def test_invoice_logger():
    """
    Test function - you can call this from Odoo shell to test logging
    Example usage in Odoo shell:

    # Create a test invoice
    partner = env['res.partner'].search([('is_company', '=', True)], limit=1)
    invoice = env['account.move'].create({
        'move_type': 'out_invoice',
        'partner_id': partner.id,
        'invoice_line_ids': [(0, 0, {
            'name': 'Test Product',
            'quantity': 1,
            'price_unit': 100,
        })]
    })
    """
    pass
