from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .num_lib import round_tariff
import logging
import json

_logger = logging.getLogger(__name__)

def allocate_customs_duties(self, customs_duties = 0.0):
    """
    Allocate customs duties to the landed cost.
    This function handles both singleton records and recordsets.
    """
    # Ensure we're working with a singleton
    self.ensure_one()
    
    # Clear existing customs fees
    self.customs_fees_ids = [(5,)]
    
    if customs_duties:
        # Define constants
        EPSILON = 0.01  # Acceptable difference
        MAX_ITERATIONS = 100  # Maximum number of iterations
        
        # Initialize variables
        iteration = 0
        best_diff = float('inf')
        best_result = None
        best_cif = 0.0  # Initialize best_cif to avoid "possibly unbound" error
        
        # Approximate value of CIF Total of the landed cost (self)
        self._compute_cost('insurance')
        self._compute_cost('freight')
        initial_cif_total = self.amount_local_currency + self.insurance + self.freight
        
        # Calculate initial customs duties to establish relationship
        result = calculate_customs_fees_for_cif_total(self, initial_cif_total)
        calculated_customs_duties = sum([it['amount'] for it in result])
        
        # Check if target is achievable by calculating at a very low CIF value
        min_cif_total = 0.01  # Start with a very small value
        min_result = calculate_customs_fees_for_cif_total(self, min_cif_total)
        min_calculated_duties = sum([it['amount'] for it in min_result])
        
        # If the minimum possible duties are still higher than the target,
        # use the minimum CIF value and log a warning
        if min_calculated_duties > customs_duties:
            _logger.warning(
                "Target customs duties (%s) is lower than the minimum achievable value (%s) with the current rates.",
                customs_duties, min_calculated_duties
            )
            # Use the minimum result directly
            for it in min_result:
                it['landed_costs_id'] = self.id
                self.customs_fees_ids = [(0, 0, it)]
            return
        
        # If we get here, the target is achievable
        lower_bound = min_cif_total  # Start with the minimum value
        upper_bound = initial_cif_total * 10
        
        # Track the best result so far from initial calculation
        current_diff = abs(customs_duties - calculated_customs_duties)
        if current_diff < best_diff:
            best_diff = current_diff
            best_result = result
            best_cif = initial_cif_total
        
        # Main loop with convergence safeguards - binary search (dichotomy)
        while abs(customs_duties - calculated_customs_duties) > EPSILON and iteration < MAX_ITERATIONS:
            iteration += 1
            
            # Calculate midpoint for binary search
            cif_total = round_tariff((lower_bound + upper_bound) / 2)
            
            # Recalculate the customs duties with the new cif_total
            result = calculate_customs_fees_for_cif_total(self, cif_total)
            calculated_customs_duties = sum([it['amount'] for it in result])
            total_calculated_cif = sum([it['cif_value'] for it in result])

            
            # Track the best result so far
            current_diff = abs(customs_duties - calculated_customs_duties)
            if current_diff < best_diff:
                best_diff = current_diff
                best_result = result
                best_cif = cif_total
            
            # Adjust bounds based on comparison
            if customs_duties > calculated_customs_duties:
                # Target is higher, search in upper half
                lower_bound = cif_total
            else:
                # Target is lower, search in lower half
                upper_bound = cif_total
                
            # Log everything for debugging
            _logger.info("++++++++++++++++++++++++++++++++++++++++")
            _logger.info("Customs Duties Calculation: Iteration %s, Target: %s, Calculated: %s, CIF Total: %s",
                            iteration, customs_duties, calculated_customs_duties, cif_total)
            _logger.info("Customs Duties Calculation: Lower Bound: %s, Upper Bound: %s", lower_bound, upper_bound)
            
            # If bounds are too close, we've reached the limit of precision
            if abs(upper_bound - lower_bound) < EPSILON:
                break
                
            _logger.debug("Customs Duties Calculation: CIF Total: %s, Result: %s, Iteration: %s, Bounds: [%s, %s]",
                         cif_total, result, iteration, lower_bound, upper_bound)
        
        # Use the best result if we didn't converge
        if (iteration >= MAX_ITERATIONS or abs(customs_duties - calculated_customs_duties) > EPSILON) and best_result:
            _logger.warning("Customs duties calculation did not converge perfectly after %s iterations. Using best approximation.",
                           iteration)
            result = best_result
            _logger.info("Best approximation: Target: %s, Calculated: %s, CIF: %s, Diff: %s",
                        customs_duties, sum([it['amount'] for it in best_result]), best_cif, best_diff)
            
        # Create customs fees records
        for it in result:
            it['landed_costs_id'] = self.id
            self.customs_fees_ids = [(0, 0, it)]
        
def calculate_customs_fees_for_cif_total(self, cif_total):
    result = []
    # Calculate the proportion of each HS code in the CIF Total
    for hs_code in set(self.received_products_ids.mapped('hs_code_id')):
        hs_code_total = sum([it.local_price_total for it in self.received_products_ids if it.hs_code_id.id == hs_code.id])
        proportion = hs_code_total / self.amount_local_currency if self.amount_local_currency else 0.0
        cif_value = cif_total * proportion
        customs_fees_id = self.env['import_fees.customs_fees'].with_context(
                no_store=True,
                default_harmonized_code_id=hs_code.id,
                default_landed_costs_id=self.id
            ).new().calculate_tariffs(recalculate=True, changes=json.dumps({"cif_value": cif_value}))
        customs_fees_id['harmonized_code_id'] = hs_code.id
        result.append(customs_fees_id)
    return result
        