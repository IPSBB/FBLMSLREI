# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import upgrades


def pre_init_hook(cr_or_env, registry=None):
    """
    Pre-init hook to handle the migration from HarmonizedCode to HarmonizedCodePerCountry.
    This function is called before the module is updated.
    """
    # Handle both cases: when cr_or_env is a cursor or an Environment object
    cr = cr_or_env.cr if hasattr(cr_or_env, 'cr') else cr_or_env
    
    # Check if the import_fees_harmonized_code table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'import_fees_harmonized_code'
        )
    """)
    harmonized_code_table_exists = cr.fetchone()[0]
    
    if not harmonized_code_table_exists:
        # If the table doesn't exist, this is a new installation, so we don't need to migrate
        return
    
    # Check if the import_fees_harmonized_code_per_country table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'import_fees_harmonized_code_per_country'
        )
    """)
    per_country_table_exists = cr.fetchone()[0]
    
    if per_country_table_exists:
        # If the table already exists, we've already migrated
        return
    
    # Create a backup of the import_fees_harmonized_code table
    cr.execute("""
        CREATE TABLE IF NOT EXISTS import_fees_harmonized_code_backup AS
        SELECT * FROM import_fees_harmonized_code;
    """)
    
    # Check if the import_fees_received_product_line table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'import_fees_received_product_line'
        )
    """)
    received_product_line_table_exists = cr.fetchone()[0]
    
    if received_product_line_table_exists:
        # Check if the hs_code_id column exists
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'import_fees_received_product_line' AND column_name = 'hs_code_id'
            )
        """)
        hs_code_id_column_exists = cr.fetchone()[0]
        
        if hs_code_id_column_exists:
            # Create a backup of the import_fees_received_product_line table
            cr.execute("""
                CREATE TABLE IF NOT EXISTS import_fees_received_product_line_backup AS
                SELECT * FROM import_fees_received_product_line;
            """)
            
            # Temporarily set hs_code_id to NULL to avoid foreign key constraint issues
            cr.execute("""
                UPDATE import_fees_received_product_line
                SET hs_code_id = NULL;
            """)


def post_init_hook(cr_or_env, registry=None):
    from odoo import api, SUPERUSER_ID
    
    # Handle both cases: when cr_or_env is a cursor or an Environment object
    if hasattr(cr_or_env, 'cr'):
        # cr_or_env is an Environment object
        env = cr_or_env
    else:
        # cr_or_env is a cursor
        env = api.Environment(cr_or_env, SUPERUSER_ID, {})
    
    # First, handle the default settings
    ResConfig = env['res.config.settings']
    default_values = ResConfig.default_get(list(ResConfig.fields_get()))

    # Case 1: Enable a group
    default_values.update({'group_multi_currency': True})
    config = ResConfig.create(default_values)
    config.execute()

    # Set default params for HS Code attribute visibility
    env['ir.config_parameter'].sudo().set_param('import_fees.cid_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.exm_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.surcharge_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.pal_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.eic_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.cess_levy_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.excise_duty_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.ridl_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.srl_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.sscl_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.vat_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.customs_bill_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.shipping_bill_visible', True)
    env['ir.config_parameter'].sudo().set_param('import_fees.add_10pc_cif', False)
    
    # Now handle the migration from HarmonizedCode to HarmonizedCodePerCountry
    cr = env.cr
    
    # Check if the backup table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'import_fees_harmonized_code_backup'
        )
    """)
    backup_table_exists = cr.fetchone()[0]
    
    if not backup_table_exists:
        # If the backup table doesn't exist, we don't need to migrate
        return
    
    # Get all records from the backup table
    cr.execute("""
        SELECT id, name, company_ids, 
               com_value, exm_value, cid_rate, surcharge_rate, pal_rate, eic_rate,
               cess_levy_rate, excise_duty_rate, ridl_rate, srl_rate, sscl_rate, vat_rate,
               create_uid, create_date, write_uid, write_date
        FROM import_fees_harmonized_code_backup
    """)
    records = cr.fetchall()
    
    # Dictionary to store old_id -> new_id mapping
    id_mapping = {}
    
    # For each record, create a new record in harmonized_code_per_country
    for record in records:
        (old_id, name, company_ids, 
         com_value, exm_value, cid_rate, surcharge_rate, pal_rate, eic_rate,
         cess_levy_rate, excise_duty_rate, ridl_rate, srl_rate, sscl_rate, vat_rate,
         create_uid, create_date, write_uid, write_date) = record
        
        # Create a new record in harmonized_code_per_country
        cr.execute("""
            INSERT INTO import_fees_harmonized_code_per_country
            (harmonized_code_id, country_id, com_value, exm_value, cid_rate, surcharge_rate, 
             pal_rate, eic_rate, cess_levy_rate, excise_duty_rate, ridl_rate, 
             srl_rate, sscl_rate, vat_rate, create_uid, create_date, write_uid, write_date)
            VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (old_id, com_value or 0.0, exm_value or 0.0, cid_rate or 0.0, surcharge_rate or 0.0, 
              pal_rate or 0.0, eic_rate or 0.0, cess_levy_rate or 0.0, excise_duty_rate or 0.0, 
              ridl_rate or 0.0, srl_rate or 0.0, sscl_rate or 0.0, vat_rate or 0.15,
              create_uid or 1, create_date or 'NOW()', write_uid or 1, write_date or 'NOW()'))
        
        new_id = cr.fetchone()[0]
        id_mapping[old_id] = new_id
    
    # Check if the import_fees_received_product_line_backup table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'import_fees_received_product_line_backup'
        )
    """)
    received_product_line_backup_exists = cr.fetchone()[0]
    
    if received_product_line_backup_exists:
        # Get all records from the backup table
        cr.execute("""
            SELECT id, hs_code_id
            FROM import_fees_received_product_line_backup
            WHERE hs_code_id IS NOT NULL
        """)
        received_product_lines = cr.fetchall()
        
        # Update the hs_code_id references in import_fees_received_product_line
        for line in received_product_lines:
            line_id, old_hs_code_id = line
            if old_hs_code_id in id_mapping:
                new_hs_code_id = id_mapping[old_hs_code_id]
                cr.execute("""
                    UPDATE import_fees_received_product_line
                    SET hs_code_id = %s
                    WHERE id = %s
                """, (new_hs_code_id, line_id))
        
        # Drop the backup table
        cr.execute("DROP TABLE IF EXISTS import_fees_received_product_line_backup")
    
    # Drop the harmonized_code backup table
    cr.execute("DROP TABLE IF EXISTS import_fees_harmonized_code_backup")
