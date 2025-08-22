/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { Product } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { BiWarningBlockingPopup } from "@bi_credit_limit_on_pos/js/Popups/BiWarningBlockingPopup";
import { BiWarningPopup } from "@bi_credit_limit_on_pos/js/Popups/BiWarningPopup";

patch(PaymentScreen.prototype, {

    setup() {
        super.setup()
        this.popup = useService("popup");
        this.orm = useService("orm");
    },

    async validateOrder(isForceValidate) {
        var self = this;
        var currentOrder = this.pos.get_order();
        var plines = currentOrder.get_paymentlines();
        var selected_lines = this.pos.get_order().selected_paymentline;
        var partner = currentOrder.get_partner();
        var a = [];
        var total_crdt = 0;

        for(var i = 0; i < plines.length; i++) {
            if(plines[i].payment_method.is_credit == true){
                total_crdt += plines[i].amount;
                a.push(plines[i]);
            }
        }

        if(currentOrder.get_orderlines().length === 0){
            self.popup.add(ErrorPopup,{
                'title': _t('Empty Order'),
                'body': _t('There must be at least one product in your order before it can be validated.'),
            });
            return;
        }

        else if (total_crdt > 0  && !currentOrder.get_partner()){
            self.popup.add(ErrorPopup,{
                'title': _t('Unknown customer'),
                'body': _t('Select customer first.'),
            });
            return;
        }

        else if (total_crdt > 0  && currentOrder.is_to_invoice()){
            self.popup.add(ErrorPopup,{
                'title': _t('Not Allowed'),
                'body': _t('Create Inovice is not allowed for Credit Payments.'),
            });
            currentOrder.set_to_invoice(false);
            return;
        }

        else if (partner){
            if(total_crdt > 0 && partner.active_credit_limit == false){
                self.popup.add(ErrorPopup,{
                    'title': _t('Not Allowed'),
                    'body': _t('Selected customer is not allowed to use credit payment.'),
                });
                return;
            }
            else if(partner.blocking_amount !== 0 && partner.active_credit_limit){
                let will_be_amt = partner.custom_credit + total_crdt;
                if (total_crdt > 0 ) {
                    if(currentOrder.get_change() > 0){
                           self.popup.add(ErrorPopup,{
                            'title': _t('Payment Amount Exceeded'),
                            'body': _t('You cannot Pay More than Total Amount'),
                        });
                        return;
                    }
                    else if(will_be_amt >= partner.blocking_amount){
                        await self.popup.add(BiWarningBlockingPopup,{
                            'title': _t('Credit Limit Exceeding'),
                            'custom_credit': partner.custom_credit,
                            'blocking_amount': partner.blocking_amount,
                        });
                        self.pos.showScreen('PaymentScreen');
                        return;
                    }
                    else if(will_be_amt >= partner.warning_amount){
                        const { confirmed, payload } = await self.popup.add(BiWarningPopup,{
                            'body': _t('The credit warning is exceeding the limit.'),
                            'custom_credit': partner.custom_credit,
                            'blocking_amount': partner.blocking_amount,
                        });
                        if (confirmed) {
                            super.validateOrder(...arguments);
                        }
                    }
                    else{
                        super.validateOrder(...arguments);
                    }
                }else{
                    super.validateOrder(...arguments);
                }
            }

            else if(partner.warning_amount == 0 && partner.warning_amount == 0 && partner.active_credit_limit){
                let credit_amt = partner.custom_credit + total_crdt;

                if(currentOrder.get_change() > 0){
                       self.popup.add(ErrorPopup,{
                        'title': _t('Payment Amount Exceeded'),
                        'body': _t('You cannot Pay More than Total Amount'),
                    });
                    return;
                }
                else if(credit_amt >= partner.blocking_amount){
                    await self.popup.add(BiWarningBlockingPopup,{
                        'title': _t('Credit Limit Exceeding'),
                        'custom_credit': partner.custom_credit,
                        'blocking_amount': partner.blocking_amount,
                    });
                    self.pos.showScreen('PaymentScreen');
                    return;
                }
                else if(credit_amt >= partner.warning_amount){
                    const { confirmed, payload } = await self.popup.add(BiWarningPopup,{
                        'body': _t('The credit warning is exceeding the limit.'),
                        'custom_credit': partner.custom_credit,
                        'blocking_amount': partner.blocking_amount,
                    });
                    if (confirmed) {
                        super.validateOrder(...arguments);
                    }
                }
                else{
                    super.validateOrder(...arguments);
                }

            }
            else{
                super.validateOrder(...arguments);
            }
        }else{
            super.validateOrder(...arguments);
        }
    }
});