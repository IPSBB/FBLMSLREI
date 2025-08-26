/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class ViewSaleOrderButton extends Component {
    static template = "wt_create_so_from_pos.ViewSaleOrderButton";
    setup() {
        this.pos = usePos();
    }
    async onClick() {
        var self = this;
        this.pos.showScreen('SaleOrderScreen');
    }
}

ProductScreen.addControlButton({
    component: ViewSaleOrderButton,
    condition: function () {
        return this.pos.config.create_so;
    },
});


// odoo.define('wt_create_so_from_pos.ViewSaleOrderButton', function(require) {
//     'use strict';

//     const PosComponent = require('point_of_sale.PosComponent');
//     const ProductScreen = require('point_of_sale.ProductScreen');
//     const { useListener } = require("@web/core/utils/hooks");
//     const Registries = require('point_of_sale.Registries');


//     class ViewSaleOrderButton extends PosComponent {
//         setup() {
//             super.setup();
//             useListener('click', this.onClick);
//         }
//         async onClick() {
//             var self = this;
//             this.showScreen('SaleOrderScreen');
//         }
//     }
//     ViewSaleOrderButton.template = 'ViewSaleOrderButton';

//     ProductScreen.addControlButton({
//         component: ViewSaleOrderButton,
//         condition: function() {
//             return this.env.pos.config.create_so;
//         },
//     });

//     Registries.Component.add(ViewSaleOrderButton);

//     return ViewSaleOrderButton;
// });
