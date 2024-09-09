/** @odoo-module */

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class ProductListItem extends Component {
    static template = "sh_pos_switch_view.ProductListItem";
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    }
    get imageUrl() {
        const product = this.props.product;
        return  `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
    }
    get pricelist() {
        const current_order = this.pos.get_order();
        if (current_order) {
            return current_order.pricelist;
        }
        return this.pos.default_pricelist;
    }
    get price() {
        const formattedUnitPrice = this.env.utils.formatCurrency(this.props.product.get_price(this.pricelist, 1), "Product Price");
        if (this.props.product.to_weight) {
            return `${formattedUnitPrice}/${this.pos.units_by_id[this.props.product.uom_id[0]].name}`;
        } else {
            return formattedUnitPrice;
        }
    }
}
