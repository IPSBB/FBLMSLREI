/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { Component, useEffect, useRef, onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(PartnerListScreen.prototype, {
    setup() {
		super.setup();
		var self = this;
		// setInterval(function(){
		// 	self.searchPartner();
		// }, 5000);
		this.searchPartner()
	},
	
    async saveChanges(processedChanges) {
        try {
            const partnerId = await this.orm.call("res.partner", "create_from_ui", [processedChanges]);
            await this.pos.load_new_partners();
            this.state.selectedPartner = this.pos.db.get_partner_by_id(partnerId);
            this.confirm();
        } catch (e) {
            console.log("-")
        }
    },  
});