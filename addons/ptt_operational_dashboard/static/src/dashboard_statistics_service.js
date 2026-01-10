/** @odoo-module **/
import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";
import { memoize } from "@web/core/utils/functions";

/**
 * Dashboard Statistics Service
 * Provides cached dashboard statistics data with reactive updates
 * Follows Odoo 19 best practices per dashboard tutorial (steps 5 & 7)
 * 
 * Reference: https://www.odoo.com/documentation/19.0/developer/tutorials/discover_js_framework/02_build_a_dashboard.html
 * 
 * Step 5: Cache network calls using memoize
 * Step 7: Use reactive objects for real-life updates (components subscribe with useState)
 */
const dashboardStatisticsService = {
    dependencies: ["orm"],
    
    start(env, { orm }) {
        // Create reactive state object (step 7: Real life update)
        // Components can subscribe to this using useState to get automatic updates
        const statistics = reactive({
            overview: null,
            reps: {},
            loading: false,
        });
        
        // Cache for promises to avoid duplicate requests
        let overviewPromise = null;
        const repPromises = new Map();
        
        /**
         * Load dashboard statistics (overview KPIs)
         * Uses memoization per tutorial step 5 - caches the promise
         * Updates reactive object in place per step 7
         */
        const loadStatistics = memoize(async () => {
            // Return cached value if available
            if (statistics.overview !== null) {
                return statistics.overview;
            }
            
            // Return existing promise if already loading
            if (overviewPromise) {
                return overviewPromise;
            }
            
            // Create new promise for loading
            statistics.loading = true;
            overviewPromise = (async () => {
                try {
                    // Get or create widget (singleton pattern)
                    let widget = await orm.searchRead(
                        'ptt.dashboard.widget',
                        [],
                        ['total_leads', 'total_quotes', 'total_events_week', 'total_outstanding', 'vendor_compliance_issues'],
                        { limit: 1 }
                    );
                    
                    if (!widget.length) {
                        // Create widget if it doesn't exist
                        const widgetId = await orm.call('ptt.dashboard.widget', '_get_or_create_widget', []);
                        widget = await orm.searchRead(
                            'ptt.dashboard.widget',
                            [['id', '=', widgetId]],
                            ['total_leads', 'total_quotes', 'total_events_week', 'total_outstanding', 'vendor_compliance_issues'],
                            { limit: 1 }
                        );
                    }
                    
                    const result = widget[0] || {};
                    // Update reactive object in place (step 7: Real life update)
                    // This triggers reactivity for components subscribed via useState
                    statistics.overview = result;
                    statistics.loading = false;
                    overviewPromise = null;
                    return result;
                } catch (error) {
                    statistics.loading = false;
                    overviewPromise = null;
                    throw error;
                }
            })();
            
            return overviewPromise;
        });
        
        /**
         * Load sales rep statistics
         * Uses memoization per tutorial step 5 - caches the promise per repId
         * Updates reactive object in place per step 7
         */
        const loadRepStatistics = memoize(async (repId) => {
            // Return cached value if available
            if (statistics.reps[repId]) {
                return statistics.reps[repId];
            }
            
            // Return existing promise if already loading
            if (repPromises.has(repId)) {
                return repPromises.get(repId);
            }
            
            // Create new promise for loading
            const promise = (async () => {
                try {
                    const rep = await orm.searchRead(
                        'ptt.sales.rep',
                        [['id', '=', repId]],
                        ['leads_count', 'quotes_count', 'events_count', 'outstanding_amount'],
                        { limit: 1 }
                    );
                    const result = rep[0] || {};
                    // Update reactive object in place (step 7: Real life update)
                    // This triggers reactivity for components subscribed via useState
                    statistics.reps[repId] = result;
                    repPromises.delete(repId);
                    return result;
                } catch (error) {
                    repPromises.delete(repId);
                    throw error;
                }
            })();
            
            repPromises.set(repId, promise);
            return promise;
        });
        
        /**
         * Invalidate cache (useful for refreshing data)
         */
        const invalidateCache = () => {
            statistics.overview = null;
            statistics.reps = {};
            overviewPromise = null;
            repPromises.clear();
        };
        
        // Return service object with reactive statistics
        // Components use useState on statisticsService.statistics to subscribe
        // Per tutorial step 7: reactive objects allow components to subscribe to changes
        return {
            statistics,
            loadStatistics,
            loadRepStatistics,
            invalidateCache,
        };
    },
};

registry.category("services").add("ptt_dashboard_statistics", dashboardStatisticsService);

