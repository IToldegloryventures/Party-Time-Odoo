/** @odoo-module **/

import { Component, onMounted, useEffect, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class KpiLayoutFour extends Component {
  static template = "ptt_dashboard.KpiLayoutFour";
  static props = {
    data: Object,
  };

  setup() {
    this.state = useState({
      data: this.props.data,
      kpi_icon: this.props.data.kpi_icon || "",
    });
    useEffect(
      () => {
        this.state.data = this.props.data;
        this.state.kpi_icon = this.props.data.kpi_icon || "";
      },
      () => [this.props.data],
    );
  }
}
