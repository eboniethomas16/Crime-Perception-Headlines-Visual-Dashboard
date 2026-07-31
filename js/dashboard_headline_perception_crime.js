// Headline/Perception/Crime Dashboard

import { drawCrimeChart } from "./dash_crime_crimeType_linechart.js";
import { drawPerceptionChart } from "./dash_perception_crimeType_linechart.js";
import { drawChordChart } from "./dash_chord_chart.js";
import { drawHeadlineHeatmap } from "./dash_heatmap_headline_crime.js";
import {drawResidualChart} from "./dash_residual_crimeType_linechart.js";
import {drawHeadlineChart} from "./dash_headline_crimeType_linechart.js";


function drawDashboard() {

    // CONTAINERS
    const residualContainer = "#chart-residual"
    const crimeContainer = "#chart-crime";
    const headlineContainer = "#chart-headlines";
    const perceptionContainer = "#chart-perception";
    const hoverListContainer = d3.select("#hoverList");
    const chordTitle = d3.select("#chordChart-title");
    chordTitle.style("display", "none");
    let useDuplicates = d3.select("#headline-toggle-duplicates").property("checked");

    const chordChartContainer = "#chordChart";
    const chordNode = document.querySelector(chordChartContainer); // chordChartContainer === "#chordChart"
    // const choroMapContainer = "#choro-map";
    const heatmapContainer = "#heatmap";

    // SHARED STATES
    let activeCrimeTypes = new Set();   // persistent selection
    let hoverCrimeType = null;          // temporary hover variable
    let snappedDate = null;           // shared hover date


    // LATEST HOVER DATA
    let latestResidualHoverData = null;
    let residualData = null;
    let aggregatedResidualData = null;
    let crimeTypeResidualData = null;
    let latestCrimeHoverData = null;
    let latestHeadlineHoverData = null;
    let latestPerceptionHoverData = null;
    let latestDate = null;
    let latestMapHoverData = null;
    let selectedHoverRow = null;     // pinned crime type
    let hoverDate = null;        // Date object snapped to quarter
    let hoverDateDisplay = null;   // formatted string: "January 2021"
    let snappedQuarterDate = null;
    let highlightLine = (crimeType) => { /* no-op until charts exist */ };
    let clearHoverHighlight = () => { /* no-op until charts exist */ };
    let nearestCrime = null;
    // let setHoverCrimeType = (crimeType) => {
    //     hoverCrimeType = crimeType;
    //     updateDashboardHoverState();
    // };

    // DATA VISUAL MODULES
    let residualChart = null;
    let crimeChart = null;
    let perceptionChart = null;
    let chordChart = null;
    let headlineChart = null;

    let heatmapModule = null;

    // DEFAULT SELECTED METRIC
    let selectedMetric = "Good job"

    function preprocessResiduals(data) {
        data.forEach(d => {
            // Parse date
            d.date = new Date(d.date);
            // Only trim crime type if it exists
            if (d.crime_type != null && d.crime_type !== "") {
                d.crime_type = d.crime_type.trim();
            }
            // Convert headline residuals
            if ("residual" in d) {
                d.residual = +d.residual;
            }
            if (d.metric) d.metric = d.metric.trim();
        });
    }

    function preprocessCrime(crimeData) {
        const parseDate = d3.timeParse("%m/%d/%Y");

        crimeData.forEach(d => {
            d.date = parseDate(d.date);

            // rename column for consistency
            d.crime_type = d.crime_type.trim();

            // your CSV uses
            d.crime_count = +d["crime_count"];
        });
    }

    function preprocessHeadlines(headlineData) {
        const parseDate = d3.timeParse("%m/%d/%Y");
        headlineData.forEach(d => {
            // parse date (expects M/D/YYYY)
            d.date = parseDate(d.date);
            // normalize text
            d.crime_type = d.crime_type.trim();
            // numeric fields (assumes valid numeric strings)
            d.avg_tone = +d.avg_tone;
            d.total_headline_count = +d.total_headline_count;
            d.total_duplicate_headline_count = +d.total_duplicate_headline_count;
        });
        return headlineData;
    }


    // perception data will aggregate after preprocessing.
    function preprocessPerception(perceptionData) {
        perceptionData.forEach(d => {
            d.date = new Date(d.date);
            d.metric_value = +d.metric_value;
            d.metric_value_pct = d.metric_value * 100;
            d.metric = d.metric.trim();
            d.borough = d.borough.trim();
        });
    }


    function preprocessHeadlineHeatmapData(heatmapData) {
        const parseDate = d3.timeParse("%m/%d/%Y");

        heatmapData.forEach(d => {
            // Parse monthly date
            d.date = parseDate(d.date);

            // Clean crime type
            d.crime_type = d.crime_type.trim();

            // Convert numbers
            d.crime_count = +d.crime_count;
            d.headline_count = +d.headline_count;
            d.signed_jsd = +d.signed_jsd;
        });
    }


    // Load BOTH datasets in parallel
    Promise.all([
        d3.csv("../data/crime_type_aggregated_residuals_monthly.csv"),      // 0
        d3.csv("../data/crime_type_residuals_monthly.csv"),     // 1 CHANGE TO CRIME TYPE RESIDUALS
        d3.csv("../data/crime_types_monthly.csv"),          // 2
        d3.csv("../data/MOPAC_FULL_LONG_Public_Perception.csv"), // 3
        d3.csv("../data/headline_daily_top3_multicrime.csv"), // 4
        d3.csv("../data/hybrid_sjsd_heatmap_crime_vs_headlines.csv"), // 5
        d3.csv("../data/crime_headlines_monthly_aggregation.csv") //6
    ]).then(([aggregatedResiduals,
                            crimeTypeResiduals,
                            crimeData,
                            perceptionData,
                            chordChartData,
                            heatmapData,
                            headlineData]) => {
        console.log("Data loaded:",
            crimeData.length,
            perceptionData.length,
            chordChartData.length,
            crimeTypeResiduals.length,
            aggregatedResiduals.length
        );


        preprocessResiduals(crimeTypeResiduals); //residuals per crime type
        preprocessResiduals(aggregatedResiduals); // single aggregate line
        preprocessCrime(crimeData);
        preprocessHeadlines(headlineData)
        preprocessHeadlineHeatmapData(heatmapData);

        // Build aggregated perception series based on the initial
        // selected metric. selected metric will be further modified inside
        // perception chart module.
        preprocessPerception(perceptionData);
        // aggregatedPerception will be an object mapping metric -> aggregated array
// aggregatedPerception = { "Good job": [{date, avg, metric}, ...], "Trust": [...], ... }
        const aggregatedPerception = Array.from(
            d3.group(perceptionData, d => (d.metric || "").trim()),
            ([metric, rows]) => {
                const agg = d3.rollups(
                    rows,
                    v => d3.mean(v, d => d.metric_value_pct),
                    d => +d.date
                )
                    .map(([ts, avg]) => ({ date: new Date(ts), avg, metric }))
                    .sort((a, b) => a.date - b.date);
                return [metric, agg];
            }
        ).reduce((acc, [metric, agg]) => {
            acc[metric] = agg;
            return acc;
        }, {});

        // Build percDataByDate as a nested lookup: Map(metric -> Map(dateMs -> avg))
// Use the same variable name `percDataByDate` throughout your codebase
        let percDataByDate = new Map();
        for (const [metric, aggArray] of Object.entries(aggregatedPerception)) {
            percDataByDate.set(metric, new Map(aggArray.map(d => [d.date.getTime(), d.avg])));
        }

// Ensure selectedMetric is valid
        if (!selectedMetric || !aggregatedPerception[selectedMetric]) {
            selectedMetric = Object.keys(aggregatedPerception)[0] || selectedMetric;
        }

        latestDate = d3.max(crimeData, d => d.date);



        const margin = { top: 20, right: 30, bottom: 40, left: 60 };

        const crimeNode = document.querySelector("#chart-crime");
        // const perceptionNode = document.querySelector("#chart-perception");
        // const choroMapNode = document.querySelector("#choro-map");

        // Line Chart container size
        const width  = crimeNode.clientWidth;
        const height = crimeNode.clientHeight;

        // inner size
        const innerWidth  = width  - margin.left - margin.right;
        const innerHeight = height - margin.top  - margin.bottom;

        // ⭐ CUT OFF ALL DATA BEFORE APRIL 1st 2017
        const cutoff = new Date(2017, 3, 1);

        const startDate = cutoff;
        const endDate = d3.max(crimeData, d => d.date);
        const fullXDomain = [startDate, endDate];
        let currentXDomain = fullXDomain;
        let hasZoomed = false;

        const x = d3.scaleTime()
            .domain(fullXDomain)
            .range([0, innerWidth]);

        // Crime y-scale
        const yCrime = d3.scaleLinear()
            .domain([0, d3.max(crimeData, d => d.crime_count)])
            .range([innerHeight, 0]);

        // Perception y-scale
        const yPerception = d3.scaleLinear()
            .domain([0, 100])
            .range([innerHeight, 0]);

        // headline y-scale
        const yHeadline = d3.scaleLinear()
            .domain([0, d3.max(headlineData, d => d.total_headline_count)])
            .range([innerHeight, 0]);



        // BUILD RESIDUAL SCALES BASED ON AGGREGATE AND CRIME TYPE RESIDUALS!
        aggregatedResidualData = aggregatedResiduals
            .filter(d => d.date >= cutoff)
            .sort((a, b) => a.date - b.date)
            .map(d => ({
                date: d.date,
                residual: d.residual,
                metric: d.metric,
            }))
            .filter(d => d.residual != null && !isNaN(d.residual));


        crimeTypeResidualData = crimeTypeResiduals
            .filter(d => d.date >= cutoff && d.metric === selectedMetric)
            .sort((a, b) => a.date - b.date)
            .map(d => ({
                crime_type: d.crime_type,
                date: d.date,
                residual: d.residual,
                metric: d.metric,
            }));

        // const crimeTypeResidualData = crimeTypeResiduals
        //     .filter(d => d.date >= cutoff)
        //     .sort((a, b) => a.date - b.date)
        //     .map(d => ({
        //         crime_type: d.crime_type,
        //         date: d.date,
        //         residual: d.residual
        //     }))
        //     .filter(d => d.residual != null && !isNaN(d.residual));


        // for residual calculations
        const allResidualData = aggregatedResidualData.concat(crimeTypeResidualData);

        const minResidual = d3.min(allResidualData, d => d.residual);
        const maxResidual = d3.max(allResidualData, d => d.residual);

        // Residual y-scale
        const yResidual = d3.scaleLinear()
            .domain([minResidual, maxResidual])
            .range([innerHeight, 0])
            .nice();

        // cutoff all data before April 2017
        crimeData = crimeData.filter(d => d.date >= cutoff);
        perceptionData = perceptionData.filter(d => d.date >= cutoff);
        heatmapData = heatmapData.filter(d => d.date >= cutoff);
        crimeTypeResiduals = crimeTypeResiduals.filter(d => d.date >= cutoff);
        aggregatedResiduals = aggregatedResiduals.filter(d => d.date >= cutoff);
        headlineData = headlineData.filter(d => d.date >= cutoff);
        chordChartData = chordChartData.filter(d => new Date(d.Day) >= cutoff);
        const chordHeadlineData = chordChartData; // rename for clarity


        // zoom logic tbd
        const resetZoomBtn = document.getElementById("resetZoomBtn");
        resetZoomBtn.addEventListener("click", () => {
            hasZoomed = false;
            resetZoomBtn.style.display = "none";
            applyXDomain(fullXDomain);
            // reset summary pills after resetting zoom
            updateSummaryPills();
        });

        // const crimeTypes = Array.from(new Set(headlineData.map(d => d.crime_type)));
        // const palette = d3.quantize(d3.interpolateSpectral, Math.max(17, crimeTypes.length));
        // // FIND NEW COLOR CODING THAT INCLUDES AT LEAST 32 DISTINCT SHADES
        // const crimeColor = d3.scaleOrdinal(palette);
        // FIND NEW COLOR CODING THAT INCLUDES AT LEAST 32 DISTINCT SHADES
        // Usage: const palette = generateBoroughPalette(32);
        function generateBoroughPalette(n, opts = {}) {
            const {
                baseChroma = 48,      // saturation-like value (0..100)
                altChroma = 30,       // alternate chroma for contrast
                baseLightness = 55,   // lightness (0..100)
                altLightness = 40,    // alternate lightness
                hueOffset = 0         // rotate starting hue if needed
            } = opts;

            const colors = [];
            for (let i = 0; i < n; i++) {
                // evenly spaced hues
                const hue = (hueOffset + (i * 360 / n)) % 360;

                // alternate chroma and lightness to increase contrast
                const chroma = (i % 2 === 0) ? baseChroma : altChroma;
                const lightness = (i % 3 === 0) ? baseLightness : altLightness;

                // d3.hcl expects (h, c, l)
                colors.push(d3.hcl(hue, chroma, lightness).formatHex());
            }
            return colors;
        }
        // from raw data array
        const boroughNames = Array.from(new Set(crimeData.map(d => d.borough))).sort();

        const palette = generateBoroughPalette(18);
        // then use palette (array of hex strings)
        // const colorScale = d3.scaleOrdinal().domain(boroughNames).range(palette);

        const crimeColor = d3.scaleOrdinal(palette);
        const perceptionColor = d3.scaleOrdinal(palette);

        //////////////////////////////
        // USE THIS FOR TOOLTIP MAPPING //
        //////////////////////////////
        const hoveredCrimeByChart = { headline: null, crime: null, residual: null, perc: null };

        //////////////////////////////
        // POPULATE Crime CHECKLIST //
        //////////////////////////////
        const crimeTypeDropdown = d3.select("#crime-type-container");
        const crimeTypeTrigger  = d3.select("#crime-type-trigger");
        const crimeTypeLabel    = d3.select("#crime-type-label");
        const crimeTypeMenu     = d3.select("#crime-type-menu");

        // 1. Extract all crime types
        const allCrimeTypes = Array.from(new Set(crimeData.map(d => d.crime_type))).sort();

        // 3. Open/close dropdown
        // stop trigger clicks from bubbling to document
        crimeTypeTrigger.on("click", (event) => {
            event.stopPropagation();
            const isOpen = crimeTypeDropdown.classed("is-open");
            crimeTypeDropdown.classed("is-open", !isOpen);
        });

        // close dropdown when clicking outside
        function onDocumentClickCloseDropdown(e) {
            const dropdownNode = document.querySelector("#crime-type-container");
            if (!dropdownNode) return;
            if (dropdownNode.contains(e.target)) return; // click inside → ignore
            crimeTypeDropdown.classed("is-open", false);
        }
        document.addEventListener("click", onDocumentClickCloseDropdown);

        // 4. Build checklist items
        const crimeTypeItems = crimeTypeMenu.selectAll(".crime-type-item")
            .data(allCrimeTypes)
            .enter()
            .append("div")
            .attr("class", "glass-dropdown-item crime-type-item")
            .each(function(type) {
                const row = d3.select(this);

                // Checkbox
                row.append("input")
                    .attr("type", "checkbox")
                    .attr("class", "crime-type-checkbox")
                    .attr("value", type)
                    .property("checked", false)   // all selected at startup
                    .property("checked", activeCrimeTypes.has(type))
                    .on("change", function() {
                        const checked = this.checked;
                        // Use your existing toggle function. Force add/remove to match checkbox.
                        toggleActiveCrimeTypes(type); // toggles
                        if (this.checked && !activeCrimeTypes.has(type)) toggleActiveCrimeTypes(type);
                        if (!this.checked && activeCrimeTypes.has(type)) toggleActiveCrimeTypes(type);
                    });

                // Label text
                row.append("span")
                    .text(type)
                    .style("cursor", "pointer")
                    .on("click", function() {
                        toggleActiveCrimeTypes(type);
                        // update checkbox DOM
                        d3.select(this.parentNode).select(".crime-type-checkbox")
                            .property("checked", activeCrimeTypes.has(type));
                    });
            });

        // 5. Update dropdown label text
        function updateCrimeTypeLabel() {
            const count = activeCrimeTypes.size;

            if (count === allCrimeTypes.length) {
                crimeTypeLabel.text("All Crime Categories Selected");
            } else if (count === 0) {
                crimeTypeLabel.text("No Crime Categories Selected");
            } else {
                crimeTypeLabel.text(`${count} Crime Categories Selected`);
            }
        }

        //////////////////////////////
        // POPULATE PERCEPTION CHECKLIST //
        //////////////////////////////
        const perceptionMetrics = Object.keys(aggregatedPerception).sort();
        if (perceptionMetrics.length === 0) perceptionMetrics.push("Default");

        const percDropdown = d3.select("#perception-metric-container");
        const percTrigger  = d3.select("#perception-metric-trigger");
        const percLabel    = d3.select("#perception-metric-label");
        const percMenu     = d3.select("#perception-metric-menu");

        if (!selectedMetric || !perceptionMetrics.includes(selectedMetric)) {
            selectedMetric = perceptionMetrics[0];
        }
        percLabel.text(selectedMetric);


        function validateSelectedMetricCandidate(candidate) {
            return typeof candidate === "string" && aggregatedPerception && !!aggregatedPerception[candidate];
        }

        function setSelectedMetric(candidate) {
            if (validateSelectedMetricCandidate(candidate)) {
                selectedMetric = candidate;
                if (typeof percLabel !== "undefined") percLabel.text(selectedMetric);
                return true;
            }
            // fallback to first valid metric
            const keys = Object.keys(aggregatedPerception || {});
            selectedMetric = keys.length ? keys[0] : selectedMetric;
            if (typeof percLabel !== "undefined") percLabel.text(selectedMetric);
            console.warn("Invalid selectedMetric prevented, reset to:", selectedMetric);
            return false;
        }

// ensure initial value is valid
        setSelectedMetric(selectedMetric);
        function buildPerceptionMenu() {
            // data join
            const sel = percMenu.selectAll(".glass-dropdown-item")
                .data(perceptionMetrics, d => d);

            // exit
            sel.exit().remove();

            // enter
            const enter = sel.enter()
                .append("button")
                .attr("type", "button")
                .attr("class", d => "glass-dropdown-item" + (d === selectedMetric ? " is-active" : ""));

            // merge enter + update so handlers/attrs apply to both
            const items = enter.merge(sel);

            // set text, active class, and click handler on merged selection
            items
                .text(d => d)
                .classed("is-active", d => d === selectedMetric)
                .on("click", (event, d) => {
                    // set metric from data only
                    setSelectedMetric(d)

                    // update label for display only
                    percLabel.text(d);

                    // visually mark active item
                    percMenu.selectAll(".glass-dropdown-item").classed("is-active", item => item === d);

                    // close dropdown
                    percDropdown.classed("is-open", false);

                    // -----------------------------
                    // Metric change: rebuild residuals + update visuals
                    // -----------------------------
                    const newAggResiduals = (aggregatedResiduals || [])
                        .filter(d => d.date >= cutoff && (!d.metric || d.metric === selectedMetric))
                        .sort((a, b) => a.date - b.date)
                        .map(d => ({ date: d.date, residual: +d.residual, metric: d.metric }));

                    const newCrimeTypeResiduals = (crimeTypeResiduals || [])
                        .filter(d => d.date >= cutoff && d.metric === selectedMetric)
                        .sort((a, b) => a.date - b.date)
                        .map(d => ({ crime_type: d.crime_type, date: d.date, residual: +d.residual, metric: d.metric }));

                    // assign into your existing top-level variables
                    aggregatedResidualData = newAggResiduals;
                    crimeTypeResidualData = newCrimeTypeResiduals;

                    // push metric-filtered arrays into the residual chart module
                    if (residualChart && typeof residualChart.updateData === "function") {
                        residualChart.updateData({
                            aggregated: aggregatedResidualData,
                            crimeTypes: crimeTypeResidualData
                        });
                    } else {
                        console.warn("residualChart.updateData not available; ensure module accepts metric-filtered arrays.");
                    }

                    // Update perception chart (existing logic)
                    if (perceptionChart && typeof perceptionChart.updateData === "function") {
                        perceptionChart.updateData(aggregatedPerception[selectedMetric] || []);
                    }
                    if (perceptionChart && typeof perceptionChart.setMetric === "function") {
                        perceptionChart.setMetric(selectedMetric);
                    }

                    // Update other visuals that depend on metric
                    if (typeof crimeChart?.redrawLines === "function") crimeChart.redrawLines();
                    if (typeof updateSummaryPills === "function") updateSummaryPills();

                    // Refresh hoverlist for current snappedDate or latest values
                    const metricMap = percDataByDate.get(selectedMetric);
                    if (snappedDate) {
                        const snappedQuarterDate = snapToQuarter(snappedDate);
                        const percHoverValue = metricMap ? metricMap.get(snappedQuarterDate.getTime()) ?? null : null;

                        const headlineHoverData = Array.from(activeCrimeTypes).map(type => {
                            const arr = headlineDataByType.get(type);
                            const row = arr?.find(r => r.date.getTime() === snappedDate.getTime());
                            return { crime_type: type, headline: row ? row[useDuplicates ? "total_duplicate_headline_count" : "total_headline_count"] : null };
                        });

                        const crimeHoverData = Array.from(activeCrimeTypes).map(type => {
                            const arr = crimeDataByType.get(type);
                            const row = arr?.find(r => r.date.getTime() === snappedDate.getTime());
                            return { crime_type: type, crime: row ? row.crime_count : null };
                        });

                        const residualHoverData = Array.from(activeCrimeTypes).map(type => {
                            const arr = aggregatedResidualData.get(type);
                            const row = arr?.find(r => r.date.getTime() === snappedDate.getTime());
                            return { crime_type: type, residual: row ? row.residual : null };
                        });

                        const mergedHoverData = mergeCrimeHeadlineResidual(
                            headlineHoverData,
                            crimeHoverData,
                            residualHoverData,
                            percHoverValue
                        );

                        updateHoverList(snappedDate, mergedHoverData, true);
                    } else {
                        showLatestValues(true);
                    }

                });
        }

        buildPerceptionMenu();

        percTrigger.on("click", (event) => {
            event.stopPropagation();
            const isOpen = percDropdown.classed("is-open");
            percDropdown.classed("is-open", !isOpen);
        });

        document.addEventListener("click", (e) => {
            const node = document.querySelector("#perception-metric-container");
            if (!node) return;
            if (!node.contains(e.target)) percDropdown.classed("is-open", false);
        });
        /////// END OF LISTENER ///////////




        //toggle for the text in the chord chart container
        function updateChordChartVisibility() {
            const msg = d3.select("#chordChart-empty-message");
            const chordTitle = d3.select("#chordChart-title");
            if (activeCrimeTypes.size === 0) {
                msg.style("display", "block");
                chordTitle.style("display", "none");
                chordChart.clear();
            } else {
                msg.style("display", "none");

                chordTitle.style("display", "flex");

            }
        }


        // ===============================
        // INITIALIZE MODULES
        // ===============================

        // Draw charts
        residualChart = drawResidualChart({
            container: residualContainer,
            aggregatedResiduals: aggregatedResidualData,   // ONE LINE
            crimeTypeResiduals: crimeTypeResidualData,      // MANY LINES
            x,
            y: yResidual,
            width,
            height,
            margin,
            color: crimeColor,
            activeCrimeTypes,
            setHoverCrimeType,
            onLineClick: toggleActiveCrimeTypes,
            onZoom: onZoom,
            onHoverCrimeType: (crimeType, event) => onChartReportedHover("residual", crimeType, event)
        });
        residualChart.initializeResidualChart();

        // Draw charts
        crimeChart = drawCrimeChart({
            container: crimeContainer,
            data: crimeData,
            x,
            y: yCrime,
            width,
            height,
            margin,
            color: crimeColor,
            activeCrimeTypes,
            setHoverCrimeType,
            onLineClick: toggleActiveCrimeTypes,
            onZoom: onZoom,
            onHoverCrimeType: (crimeType, event) => onChartReportedHover("crime", crimeType, event)
        });
        crimeChart.dim(true);   // crime chart start dimmed

        headlineChart = drawHeadlineChart({
            container: headlineContainer,            // e.g. "#headlineChart" or a DOM node
            data: headlineData,                      // [{ date, crime_type, avg_tone, total_headline_count, total_duplicate_headline_count }]
            x: x,                                    // your time scale
            y: yHeadline,                            // your y scale for avg_tone
            width: width,
            height: height,
            margin: margin,
            color: crimeColor,
            useDuplicates: useDuplicates,
            onLineClick: (crimeType) => {
                // optional: handle clicks on a crime-type line
                console.log("headline line clicked:", crimeType);
                // e.g. update active sets or sync other charts
            },
            onZoom: onZoom,
            onHoverCrimeType: (crimeType, event) => onChartReportedHover("headline", crimeType, event)
        });
        headlineChart.dim(true);
        headlineChart.initializeHeadlineChart();
        // headlineChart.dim(true);   // headline chart start dimmed
        /////////////////////////////////////////////
        // listener for headline duplicate checkbox
        /////////////////////////////////////////////
        d3.select("#headline-toggle-duplicates").on("change", function() {
            // 1) update dashboard state
            const checked = d3.select(this).property("checked");
            useDuplicates = checked;
            // update the headline summary pill title immediately
            d3.select("#headline-summary-pill .summary-title")
                .text(checked ? "Total Duplicated Headline Count" : "Total Headline Count");

            // 2) inform headline chart once (chart will update any count-dependent UI)
            if (headlineChart && typeof headlineChart.setUseDuplicates === "function") {
                headlineChart.setUseDuplicates(checked);
            }

            // 3) ensure headline chart recomputes y-domain for the current active set
            if (headlineChart && typeof headlineChart.updateActiveCrimeTypes === "function") {
                headlineChart.updateActiveCrimeTypes(activeCrimeTypes);
            }

            // 4) if there's an active hover/snapped date, recompute all hover arrays and merge
            if (snappedDate) {
                const field = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";

                const headlineHoverData = Array.from(activeCrimeTypes).map(type => {
                    const arr = headlineDataByType.get(type);
                    const row = arr?.find(d => d.date.getTime() === snappedDate.getTime());
                    return { crime_type: type, headline: row ? row[field] : null };
                });

                const crimeHoverData = Array.from(activeCrimeTypes).map(type => {
                    const arr = crimeDataByType.get(type);
                    const row = arr?.find(d => d.date.getTime() === snappedDate.getTime());
                    return { crime_type: type, crime: row ? row.crime_count : null };
                });

                const residualHoverData = Array.from(activeCrimeTypes).map(type => {
                    const arr = crimeTypeResidualData.get(type);
                    const row = arr?.find(d => d.date.getTime() === snappedDate.getTime());
                    return { crime_type: type, residual: row ? row.residual : null };
                });

                const snappedQuarterDate = snapToQuarter(snappedDate);
                let percHoverValue = null;
                const metricMap = percDataByDate.get(selectedMetric);
                if (metricMap) {
                    percHoverValue = metricMap.get(snappedQuarterDate.getTime()) ?? null;
                } else {
                    const arr = aggregatedPerception[selectedMetric] || [];
                    const pRow = arr.find(p => p.date && p.date.getTime() === snappedQuarterDate.getTime());
                    percHoverValue = pRow ? pRow.avg : null;
                }


                const mergedHoverData = mergeCrimeHeadlineResidual(
                    headlineHoverData,
                    crimeHoverData,
                    residualHoverData,
                    percHoverValue
                );

                // 5) update dashboard-level latest values and UI
                latestHeadlineHoverData = headlineHoverData;
                latestCrimeHoverData = crimeHoverData;
                latestResidualHoverData = residualHoverData;
                latestPerceptionHoverData = percHoverValue;

                updateHoverList(snappedDate, mergedHoverData, true);
            } else {
                // 6) no hover active → refresh latest summary values
                showLatestValues(true);
            }

            // 7) refresh summary pills
            updateSummaryPills();
        });


        // initial aggregated array for the perception module (keeps old name usage minimal)
        const initialAggregatedPerception = aggregatedPerception[selectedMetric] || [];
        // aggregated perception chart drawing
        perceptionChart = drawPerceptionChart({
            container: perceptionContainer,
            data: initialAggregatedPerception,   // MODULE FILTERS BY METRIC
            x,
            y: yPerception,
            width,
            height,
            margin,
            color: perceptionColor,
            onZoom: onZoom,
            onHoverCrimeType: (crimeType, event) => onChartReportedHover("perception", crimeType, event)
        });
        perceptionChart.initializePerceptionChart(selectedMetric);
        // if (typeof perceptionChart.initializePerceptionChart === "function") {
        //     perceptionChart.initializePerceptionChart(selectedMetric);
        // }
        // if (typeof perceptionChart.updateData === "function") {
        //     perceptionChart.updateData(initialAggregatedPerception);
        // }


        heatmapModule = drawHeadlineHeatmap({
            container: "#heatmap",
            data: heatmapData,
            activeCrimeTypes,
            setHoverCrimeType,
            setHoverDate,            // monthly hover
            onHeatmapHoverCell,
            updateDashboardHoverState,
            onClick: (crimeType) => {
                // toggle via your existing function
                toggleActiveCrimeTypes(crimeType);

                // sync checklist DOM to reflect the new active set
                crimeTypeMenu.selectAll(".crime-type-checkbox")
                    .property("checked", function () {
                        return activeCrimeTypes.has(this.value);
                    });
            }
        });

        chordChart = drawChordChart({
            container: chordChartContainer,
            data: chordChartData,   // raw headline rows
            width: chordNode.clientWidth,
            height: chordNode.clientHeight,
            color: crimeColor
        });

        ///////////////////////////////////////////////////////////////////////
        // HOVERLINE LOGIC + LISTENERS
        ///////////////////////////////////////////////////////////////////////
        // Initialize hoverList with instructional title


        // Variables for the hoverLine and hoverlist
        allResidualData.sort((a, b) => a.date - b.date); // ensure data is sorted by date
        const residualDataByCrimeType = d3.group(crimeTypeResidualData, d => d.crime_type);
        const crimeDataByType = d3.group(crimeData, d => d.crime_type);
        const headlineDataByType = d3.group(headlineData, d => d.crime_type);
        // aggregated perception hover
        // percDataByDate = new Map(
        //     aggregatedPerception.map(d => [d.date.getTime(), d.avg])
        // );
        // aggregatedPerception[metric] -> [{ date: Date, avg, metric }, ...]

        // Build once after aggregation (do not redeclare later)
        percDataByDate = new Map();
        for (const metric of Object.keys(aggregatedPerception)) {
            const arr = aggregatedPerception[metric] || [];
            percDataByDate.set(metric, new Map(arr.map(d => [d.date.getTime(), d.avg])));
        }


        const plotGroupNode = residualChart.plotGroupNode;
        const lineChartsNode = document.querySelector("#line-charts");


        const hoverLineHeadline = d3.select(headlineChart.plotGroupNode)
            .append("line")
            .attr("class", "hover-line")
            .attr("y1", 0)
            .attr("y2", innerHeight +400)
            .style("opacity", 0)
            .raise();

        const hoverLineResidual = d3.select(residualChart.plotGroupNode)
            .append("line")
            .attr("class", "hover-line")
            .attr("y1", 0)
            .attr("y2", innerHeight + 400)
            .style("opacity", 0)
            .raise();

        const hoverLineCrime = d3.select(crimeChart.plotGroupNode)
            .append("line")
            .attr("class", "hover-line")
            .attr("y1", 0)
            .attr("y2", innerHeight +400)
            .style("opacity", 0)
            .raise();
        const hoverLinePerc = d3.select(perceptionChart.plotGroupNode)
            .append("line")
            .attr("class", "hover-line")
            .attr("y1", 0)
            .attr("y2", innerHeight +400)
            .style("opacity", 0)
            .raise();

        //set the latest values: (WILL CHANGE LATER WHEN SNAPPING FUNCTIONALITY IS INTRODUCED)
        latestCrimeHoverData = Array.from(activeCrimeTypes).map(type => {
            const arr = crimeDataByType.get(type);
            const row = arr?.find(d => d.date.getTime() === latestDate.getTime());
            return {
                crime_type: type,
                crime: row ? row.crime_count : null
            };
        });

        // check the toggle (true => show duplicate headline counts; false => show total headline counts)


        function computeLatestPerceptionHoverData() {
            // Ensure selectedMetric is valid
            if (!selectedMetric || !aggregatedPerception[selectedMetric]) {
                const keys = Object.keys(aggregatedPerception || {});
                selectedMetric = keys.length ? keys[0] : selectedMetric;
                percLabel.text(selectedMetric);
            }

            // If no latestDate yet, nothing to compute
            if (!latestDate) {
                latestPerceptionHoverData = null;
                return latestPerceptionHoverData;
            }

            // Snap latestDate (monthly) to the quarter used by perception data
            const latestQuarterDate = snapToQuarter(latestDate);
            const ts = latestQuarterDate.getTime();

            // Lookup using nested Map (this is your primary source)
            // const metricMap = percDataByDate.get(selectedMetric);
            // if (metricMap) {
            //     latestPerceptionHoverData = metricMap.get(ts) ?? null;
            //     return latestPerceptionHoverData;
            // }

            // Fallback: aggregatedPerception array (compare timestamps!)
            const arr = aggregatedPerception[selectedMetric] || [];
            const pRow = arr.find(p => p.date && p.date.getTime() === ts);
            latestPerceptionHoverData = pRow ? pRow.avg : null;

            return latestPerceptionHoverData;
        }



        latestHeadlineHoverData = Array.from(activeCrimeTypes).map(type => {
            const arr = headlineDataByType.get(type);
            if (!arr) return { crime_type: type, crime: null };
            // choose the field based on the toggle
            const field = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";
            // find the row for the latest date
            const row = arr.find(d => d.date.getTime() === latestDate.getTime());
            return {
                crime_type: type,
                crime: row ? row[field] : null
            };
        });


        latestResidualHoverData = Array.from(activeCrimeTypes).map(type => {
            const arr = residualDataByCrimeType.get(type);
            const row = arr?.find(d => d.date.getTime() === latestDate.getTime());
            return {
                crime_type: type,
                residual: row ? row.residual : null
            };
        });

        const latestMetricMap = percDataByDate.get(selectedMetric);
        latestPerceptionHoverData = latestMetricMap ? latestMetricMap.get(latestDate.getTime()) ?? null : null;


        function latestMergedHoverData() {
            let mergedArray = null;
            mergedArray = mergeCrimeHeadlineResidual(
                latestHeadlineHoverData,
                latestCrimeHoverData,
                latestResidualHoverData,
                latestPerceptionHoverData
            );
            return mergedArray
        }

        showLatestValues(true)
        // updateHoverList(null, [], null);
        // 3. Build hoverlist using real data
        updateHoverList(latestDate, latestMergedHoverData(), false);
        updateDashboardHoverState();


        // UPDATES THE HOVERLINE LISTENER
        // helper: snap a Date down to the quarter start (Jan/Apr/Jul/Oct)
        function snapToQuarter(date) {
            const month = date.getMonth();
            const quarterStartMonth = month < 3 ? 0 : month < 6 ? 3 : month < 9 ? 6 : 9;
            return new Date(date.getFullYear(), quarterStartMonth, 1);
        }
        //
        // // Returns "headline" | "crime" | "residual" | "perc" or null
        // function chartNameUnderPointer(event) {
        //     if (!event) return null;
        //     const cx = event.clientX;
        //     const cy = event.clientY;
        //     if (cx == null || cy == null) return null;
        //
        //     // 1) Prefer elementsFromPoint so we can inspect the full stack under the pointer
        //     let els = [];
        //     try {
        //         els = document.elementsFromPoint(cx, cy) || [];
        //     } catch (e) {
        //         // elementsFromPoint may throw in some older browsers; fall back to elementFromPoint
        //         const el = document.elementFromPoint(cx, cy);
        //         if (el) els = [el];
        //     }
        //
        //     // helper to test an element or its ancestors for a selector
        //     const closestMatch = (el, selector) => {
        //         if (!el) return null;
        //         if (el.closest) return el.closest(selector);
        //         // fallback: walk up manually
        //         let cur = el;
        //         while (cur) {
        //             if (cur.matches && cur.matches(selector)) return cur;
        //             cur = cur.parentElement;
        //         }
        //         return null;
        //     };
        //
        //     // check the stacked elements for a matching chart container
        //     for (const el of els) {
        //         if (!el) continue;
        //         if (closestMatch(el, "#chart-headlines")) return "headline";
        //         if (closestMatch(el, "#chart-crime"))     return "crime";
        //         if (closestMatch(el, "#chart-residual"))  return "residual";
        //         if (closestMatch(el, "#chart-perception"))return "perc";
        //     }
        //
        //     // 2) Fallback: check container bounding rects (useful if an overlay intercepts pointer events)
        //     const containers = [
        //         { name: "headline", selector: "#chart-headlines" },
        //         { name: "crime",    selector: "#chart-crime" },
        //         { name: "residual", selector: "#chart-residual" },
        //         { name: "perc",     selector: "#chart-perception" }
        //     ];
        //
        //     for (const c of containers) {
        //         const node = document.querySelector(c.selector);
        //         if (!node) continue;
        //         const r = node.getBoundingClientRect();
        //         if (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) return c.name;
        //     }
        //
        //     // 3) Nothing matched
        //     return null;
        // }




        // Central handler called by each chart module via onHoverCrimeType(chartName)
        function onChartReportedHover(chartName, crimeType, event) {
            // keep per-chart map (optional but useful for debugging)
            hoveredCrimeByChart[chartName] = crimeType;

            // update the global hover variable used by updateDashboardHoverState
            hoverCrimeType = crimeType;

            // If you want hovering to clear a pinned selection, do it here:
            // selectedHoverRow = selectedHoverRow && crimeType === selectedHoverRow ? selectedHoverRow : selectedHoverRow;

            // Refresh dashboard highlights / hoverlist / hoverlines
            updateDashboardHoverState();

            // Optionally show tiny local tooltips in all charts for the same crime type
            // (each chart's showHoverTooltip should accept (crimeType, event) and position locally)
            if (crimeType) {
                if (typeof headlineChart?.showHoverTooltip === "function") headlineChart.showHoverTooltip(crimeType, event);
                // if (typeof crimeChart?.showHoverTooltip === "function")    crimeChart.showHoverTooltip(crimeType, event);
                // if (typeof residualChart?.showHoverTooltip === "function") residualChart.showHoverTooltip(crimeType, event);
                // if (typeof percChart?.showHoverTooltip === "function")     percChart.showHoverTooltip(crimeType, event);
            } else {
                // hide all local tooltips when pointer leaves
                headlineChart?.hideHoverTooltip?.();
                // crimeChart?.hideHoverTooltip?.();
                // residualChart?.hideHoverTooltip?.();
                // percChart?.hideHoverTooltip?.();
            }
        }

        // unified mousemove handler for line charts
        function onLineChartsMouseMove(event) {
            // if no crime types active, don't do anything
            if (activeCrimeTypes.size === 0) return;
            if (!residualDataByCrimeType.size) return;

            // pointer relative to the plot group
            const [mx] = d3.pointer(event, plotGroupNode);
            const rawDate = x.invert(mx);

            // 1) Snap to nearest monthly crime date using the first active series that has data
            let snappedCrimeDate = rawDate;
            const firstActiveCrimeSeries = Array.from(activeCrimeTypes)
                .map(type => crimeDataByType.get(type))
                .find(arr => arr && arr.length > 0);

            if (firstActiveCrimeSeries) {
                const closestCrime = firstActiveCrimeSeries.reduce((a, c) =>
                    Math.abs(c.date - rawDate) < Math.abs(a.date - rawDate) ? c : a
                );
                snappedCrimeDate = closestCrime.date;
            }

            // 2) Snap perception date down to quarter
            const snappedQuarterDate = snapToQuarter(snappedCrimeDate);

            // 3) Update global hover state (monthly for heatmap)
            setHoverDate(snappedCrimeDate);   // this should set hoverDate and call updateDashboardHoverState()

            // 4) Move hover lines (monthly position)
            const snappedX = x(snappedCrimeDate);
            hoverLineHeadline
                .attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1).raise();
            hoverLineResidual
                .attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1).raise();
            hoverLineCrime
                .attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1).raise();
            hoverLinePerc
                .attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1).raise();

            // 5) Build headline hover data (monthly)
            const headlineField = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";
            const headlineHoverData = Array.from(activeCrimeTypes).map(type => {
                const arr = headlineDataByType.get(type);
                const row = arr?.find(d => d.date.getTime() === snappedCrimeDate.getTime());
                return { crime_type: type, headline_count: row ? row[headlineField] : null };
            });

            // 6) Build crime hover data (monthly)
            const crimeHoverData = Array.from(activeCrimeTypes).map(type => {
                const arr = crimeDataByType.get(type);
                const row = arr?.find(d => d.date.getTime() === snappedCrimeDate.getTime());
                return { crime_type: type, crime: row ? row.crime_count : null };
            });

            // 7) Perception: read single aggregated value for the quarter
            // Prefer percDataByDate Map keyed by timestamp; fallback to aggregatedPerception array
            let percHoverValue = null;
            const metricMap = percDataByDate.get(selectedMetric); // percDataByDate is Map(metric -> Map)
            if (metricMap) {
                percHoverValue = metricMap.get(snappedQuarterDate.getTime()) ?? null;
            } else {
                // fallback: if you still have an aggregatedPerception object, try to find the row
                const arr = aggregatedPerception[selectedMetric] || [];
                const pRow = arr.find(p => p.date && p.date.getTime() === snappedQuarterDate.getTime());
                percHoverValue = pRow ? pRow.avg : null;
            }

            // Residual values at snappedQuarterDate (quarter lookup)
            const residualHoverData = Array.from(activeCrimeTypes).map(type => {
                const arr = (crimeTypeResidualData || []).filter(r => r.crime_type === type);
                if (!arr || arr.length === 0) return { crime_type: type, residual: null };

                let row = arr.find(r => r.date && r.date.getTime() === snappedQuarterDate.getTime());
                if (!row) {
                    row = arr.reduce((best, cur) => {
                        if (!best) return cur;
                        return Math.abs(cur.date - snappedQuarterDate.getTime()) < Math.abs(best.date - snappedQuarterDate.getTime()) ? cur : best;
                    }, null);
                }
                return { crime_type: type, residual: row ? row.residual : null };
            });

            // 8) Merge using your existing helper (crimeArr, residualArr, perceptionValue)
            const mergedHoverData = mergeCrimeHeadlineResidual(
                headlineHoverData,
                crimeHoverData,
                residualHoverData,
                percHoverValue
            );

            // 9) Store latest hover data for other UI consumers
            latestHeadlineHoverData = headlineHoverData;
            latestCrimeHoverData = crimeHoverData;
            latestResidualHoverData = residualHoverData;
            latestPerceptionHoverData = percHoverValue;
            snappedDate = snappedCrimeDate;

            // 10) Update hover list and dashboard
            updateHoverList(snappedCrimeDate, mergedHoverData, true);
        }


//
//         let rafPending = false;
//         let lastMouseEvent = null;
//
//         function scheduleLineChartsMouseMove(event) {
//             lastMouseEvent = event;
//             if (!rafPending) {
//                 rafPending = true;
//                 requestAnimationFrame(() => {
//                     rafPending = false;
//                     onLineChartsMouseMove(lastMouseEvent);
//                 });
//             }
//         }
//
// // attach the throttled handler to the container that receives pointer events
//
//         lineChartsNode.addEventListener("mousemove", scheduleLineChartsMouseMove);
//         lineChartsNode.addEventListener("pointermove", scheduleLineChartsMouseMove); // optional


        // attach handlers (replace your existing addEventListener blocks)
        lineChartsNode.addEventListener("mousemove", onLineChartsMouseMove);

        lineChartsNode.addEventListener("mouseleave", () => {
            hoverLineHeadline.style("opacity", 0);
            hoverLineCrime.style("opacity", 0);
            hoverLinePerc.style("opacity", 0);
            hoverLineResidual.style("opacity", 0);

            // clear per-chart reported hover state (modules should also call onHoverCrimeType(null) on their own leave)
            hoveredCrimeByChart.headline = null;
            hoveredCrimeByChart.crime = null;
            hoveredCrimeByChart.residual = null;
            hoveredCrimeByChart.perc = null;

            // hide all tooltips
            if (headlineChart?.hideHoverTooltip) headlineChart.hideHoverTooltip();
            if (crimeChart?.hideHoverTooltip)    crimeChart.hideHoverTooltip();
            if (residualChart?.hideHoverTooltip) residualChart.hideHoverTooltip();
            if (perceptionChart?.hideHoverTooltip)     perceptionChart.hideHoverTooltip();

            // reset hover state used elsewhere
            hoverDate = null;
            hoverCrimeType = null;
            if (activeCrimeTypes.size > 0) {
                showLatestValues(true);
            } else {
                showLatestValues(false);
            }
            updateDashboardHoverState();
        });


        // HEATMAP MOUSE LISTENERS
        const heatmapNode = document.querySelector("#heatmap-scroll-wrapper");

        heatmapNode.addEventListener("mouseleave", () => {

            // 1. Clear hover state
            hoverCrimeType = null;
            hoverDate = null;

            // 2. Clear heatmap visual hover
            heatmapModule.clearCellHover();
            heatmapModule.clearHoverHighlight();

            // NEW? MAYBE DELETE
            // 3. Clear hoverlines on ALL charts
            hoverLineHeadline.style("opacity", 0);
            hoverLineCrime.style("opacity", 0);
            hoverLinePerc.style("opacity", 0);
            hoverLineResidual.style("opacity", 0);

            // 3. Show latest values (if any crime types selected)
            if (activeCrimeTypes.size > 0) {
                showLatestValues(true);
            } else {
                showLatestValues(false);
            }

            // 4. Update dashboard titles + choromap + hoverline
            updateDashboardHoverState();
        });



        //inputs:
        // crimeArr → monthly crime counts by crime_type
        // headlineArr → headline counts by crime_type
        // residualArr → your new residuals by crime_type

        function mergeCrimeHeadlineResidual(
            headlineArr = [],
            crimeArr = [],
            residualArr = [],
            perceptionValue = null
        ) {
            const merged = crimeArr.map(c => {
                const type = c.crime_type;

                // ⭐ crime lookup variable (c is the crime row)
                const crimeRow = c;

                // find matching residual row
                const r = residualArr.find(x => x.crime_type === type);

                // find matching headline row (accept multiple possible field names)
                const h = headlineArr.find(x => x.crime_type === type);
                const headlineVal = h
                    ? (h.headline_count ?? h.crime ?? h.headline ?? null)
                    : null;

                // round helpers that preserve null/undefined
                const roundPerception = val =>
                    val === null || val === undefined ? null : +Number(val).toFixed(1);

                const roundResidual = val =>
                    val === null || val === undefined ? null : +Number(val).toFixed(2);

                return {
                    crime_type: type,
                    crime: crimeRow.crime ?? null,
                    headline: headlineVal,
                    residual: r && r.residual != null ? roundResidual(r.residual) : null,
                    perception: roundPerception(perceptionValue)
                };
            });

            return merged;
        }


        ///////////////////////////////////////////////////////////////////////
        // core update functions
        ///////////////////////////////////////////////////////////////////////
        function toggleActiveCrimeTypes(crimeTypeName) {
            // Toggle membership
            if (activeCrimeTypes.has(crimeTypeName)) {
                activeCrimeTypes.delete(crimeTypeName);
            } else {
                activeCrimeTypes.add(crimeTypeName);
            }

            crimeChart.dim(activeCrimeTypes.size === 0);
            residualChart.dim(activeCrimeTypes.size === 0);
            // headlineChart.dim(activeCrimeTypes.size === 0);

            // Apply persistent active/dimmed styling
            updateDashboardActiveState();
            // update the summary pills to reflect new active crime type
            updateSummaryPills();

            updateCrimeTypeLabel();
            updateChordChartVisibility()
        }

        ///////////////////////////////////////////////////////////////////////
        // ZOOM FUNCTIONS
        ///////////////////////////////////////////////////////////////////////
        function applyXDomain(domain) {
            currentXDomain = domain;

            // 1. Update both charts
            residualChart.applyXDomain(domain)
            headlineChart.applyXDomain(domain)
            crimeChart.applyXDomain(domain);
            perceptionChart.applyXDomain(domain);

            // 2. Update heatmap to show only columns in this domain
            heatmapModule.updateDateDomain(domain);
            // if (heatmapModule) {
            //     heatmapModule.updateDateDomain(domain);
            // }

            // 3. Keep hoverline logic as-is (x scale is updated inside charts)
            showLatestValues(true);
        }

        function onZoom(domain) {
            hasZoomed = true;
            resetZoomBtn.style.display = "inline-block";
            applyXDomain(domain);
            // update summary pills after zooming on line charts
            updateSummaryPills();
        }


        function updatePerceptionMetric() {
            // -----------------------------
            // 1. Update Perception/Crime line charts
            // -----------------------------

            const filteredPerception = perceptionData.filter(d => d.metric === selectedMetric);

            // perceptionChart.initializePerceptionChart(selectedMetric)
            // update the perception chart line to new perception metric
            perceptionChart.updateData(filteredPerception);

            // update BOTH charts' x-axis
            perceptionChart.redrawXAxis();

            //only perception lines need to be redrawn
            // perceptionChart.redrawLines();
            crimeChart.redrawLines();


            // If hovering a quarter, update hoverline position
            if (hoverDate) {
                const snappedX = x(hoverDate);
                hoverLineResidual
                    .attr("x1", snappedX)
                    .attr("x2", snappedX)
                    .style("opacity", 1)
                    .raise();
            }


            showLatestValues(true);
        }

        // UPDATE PERCEPTION METRIC + SUMMARY PILLS
        // AS SOON AS WINDOW LOADS
        // updatePerceptionMetric();
        updateSummaryPills();

        // SUMMARY PILL FUNCTIONS
        function computeCrimeTotal(crimeData, crimeTypes, dateDomain) {
            const [d0, d1] = dateDomain;

            return crimeData
                .filter(d => crimeTypes.has(d.crime_type))
                .filter(d => d.date >= d0 && d.date <= d1)
                .reduce((sum, d) => sum + d.crime_count, 0);
        }

        function computeHeadlineTotal(headlineData, crimeTypes, dateDomain, useDuplicates) {
            const [d0, d1] = dateDomain;
            const field = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";

            const filtered = headlineData
                .filter(d => crimeTypes.has(d.crime_type))
                .filter(d => d.date >= d0 && d.date <= d1)
                .map(d => +d[field]);

            if (filtered.length === 0) return null;

            return filtered.reduce((sum, v) => sum + (isNaN(v) ? 0 : v), 0);
        }

        function computeCrime12MonthChange(crimeData, crimeTypes) {

            const latestDate = d3.max(crimeData, d => d.date);
            const oneYearAgo = d3.timeMonth.offset(latestDate, -12);
            const twoYearsAgo = d3.timeMonth.offset(latestDate, -24);

            const currentPeriod = crimeData
                .filter(d => crimeTypes.has(d.crime_type))
                .filter(d => d.date > oneYearAgo && d.date <= latestDate)
                .reduce((sum, d) => sum + d.crime_count, 0);

            const previousPeriod = crimeData
                .filter(d => crimeTypes.has(d.crime_type))
                .filter(d => d.date > twoYearsAgo && d.date <= oneYearAgo)
                .reduce((sum, d) => sum + d.crime_count, 0);

            if (previousPeriod === 0) return null;

            return ((currentPeriod - previousPeriod) / previousPeriod) * 100;
        }

        function computePerceptionAvgAggregated(aggregatedPerception, dateDomain) {
            const [d0, d1] = dateDomain;

            const filtered = aggregatedPerception
                .filter(d => d.date >= d0 && d.date <= d1)
                .map(d => d.avg);

            return d3.mean(filtered);
        }

        function computeHeadline12MonthChange(headlineData, crimeTypes, useDuplicates) {
            const field = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";

            // restrict to relevant crime types
            const filtered = headlineData.filter(d => crimeTypes.has(d.crime_type));

            if (!filtered.length) return null;

            const latestDate = d3.max(filtered, d => d.date);
            const oneYearAgo = d3.timeMonth.offset(latestDate, -12);
            const twoYearsAgo = d3.timeMonth.offset(latestDate, -24);

            const currentPeriod = filtered
                .filter(d => d.date > oneYearAgo && d.date <= latestDate)
                .reduce((sum, d) => sum + (+d[field] || 0), 0);

            const previousPeriod = filtered
                .filter(d => d.date > twoYearsAgo && d.date <= oneYearAgo)
                .reduce((sum, d) => sum + (+d[field] || 0), 0);

            if (previousPeriod === 0) return null;

            return ((currentPeriod - previousPeriod) / previousPeriod) * 100;
        }

        function updateSummaryPills() {

            const crimeTypes = activeCrimeTypes.size > 0
                ? activeCrimeTypes
                : new Set(crimeData.map(d => d.crime_type));

            const dateDomain = currentXDomain || fullXDomain;

            const crimeTotal = computeCrimeTotal(crimeData, crimeTypes, dateDomain);
            const headlineTotal = computeHeadlineTotal(headlineData, crimeTypes, dateDomain, useDuplicates);
            const crimeChange = computeCrime12MonthChange(crimeData, crimeTypes);
            const headlineChange = computeHeadline12MonthChange(headlineData, crimeTypes, useDuplicates);

            // MAIN VALUES
            d3.select("#crime-summary-value").text(crimeTotal.toLocaleString());
            d3.select("#headline-summary-value").text(headlineTotal.toLocaleString());

            // RESET CHANGE PILL CLASSES
            d3.select("#crime-change-value").attr("class", "change-value");
            d3.select("#headline-change-value").attr("class", "change-value");

            // CRIME CHANGE ARROW LOGIC
            if (crimeChange != null) {
                const arrow = crimeChange >= 0 ? "▲" : "▼";
                const colorClass = crimeChange >= 0 ? "arrow-up-red" : "arrow-down-green";
                d3.select("#crime-change-value")
                    .attr("class", `change-value ${colorClass}`)
                    .text(`${arrow} ${Math.abs(crimeChange).toFixed(1)}%`);
            }

            // HEADLINE CHANGE ARROW LOGIC (uses headlineChange)
            if (headlineChange != null) {
                const arrow = headlineChange >= 0 ? "▲" : "▼";
                const colorClass = headlineChange >= 0 ? "arrow-up-red" : "arrow-down-green";
                d3.select("#headline-change-value")
                    .attr("class", `change-value ${colorClass}`)
                    .text(`${arrow} ${Math.abs(headlineChange).toFixed(1)}%`);
            } else {
                d3.select("#headline-change-value").text("—");
            }
        }


        // SHOW THE MOST RECENT CRIME AND PERCEPTION VALUES IN THE HOVERLIST
        function showLatestValues(showDate = true) {
            computeLatestPerceptionHoverData();
            // ---------------------------------------------
            // 0. If nothing selected → clear hoverlist
            // ---------------------------------------------
            if (activeCrimeTypes.size === 0) {
                latestDate = d3.max(crimeData, d => d.date);
                updateHoverList(null, [], null);
                return;
            }
            // ---------------------------------------------
            // 1. Latest CRIME values (monthly)
            // ---------------------------------------------
            const crimeLatest = Array.from(activeCrimeTypes).map(type => {
                const arr = crimeDataByType.get(type);
                if (!arr || arr.length === 0) return { crime_type: type, crime: null };

                const last = arr[arr.length - 1];
                return {
                    crime_type: type,
                    crime: last.crime_count
                };
            });
            // ---------------------------------------------
            // 2. Latest HEADLINE values (daily → aggregated monthly)
            // (You will create headlineDataByCrimeType)
            // ---------------------------------------------
            const headlineField = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";

            const headlineLatest = Array.from(activeCrimeTypes).map(type => {
                const arr = headlineDataByType.get(type);
                if (!arr || arr.length === 0) return { crime_type: type, headline_count: null };

                const last = arr[arr.length - 1];
                return {
                    crime_type: type,
                    headline_count: last[headlineField] ?? null
                };
            });

            // ---------------------------------------------
            // 3. Latest RESIDUAL values (monthly)
            // ---------------------------------------------

            const residualLatest = Array.from(activeCrimeTypes).map(crimeType => {
                const arr = (crimeTypeResidualData || []).filter(r => r.crime_type === crimeType);
                if (!arr || arr.length === 0) return { crime_type: crimeType, residual: null };

                // arr is sorted by date; last element is the most recent quarter for this metric
                const last = arr[arr.length - 1];
                return {
                    crime_type: crimeType,
                    residual: last ? last.residual : null
                };
            });
            // const residualLatest = Array.from(activeCrimeTypes).map(type => {
            //     const arr = residualDataByCrimeType.get(type);
            //     if (!arr || arr.length === 0) return { crime_type: type, residual: null };
            //
            //     const last = arr[arr.length - 1];
            //     return {
            //         crime_type: type,
            //         residual: last.residual
            //     };
            // });

            // ---------------------------------------------
            // 4. Latest aggregated PERCEPTION value (single number)
            // ---------------------------------------------
            const latestPerception = aggregatedPerception[aggregatedPerception.length - 1]?.avg ?? null;

            // ---------------------------------------------
            // 5. Merge crime + headline + residual into unified rows
            //    Use the shared merge helper instead of inlining
            // ---------------------------------------------
            // mergeCrimeHeadlineResidual expects: (crimeArr, residualArr, perceptionValue)
            const mergedLatest = mergeCrimeHeadlineResidual(
                headlineLatest,
                crimeLatest,
                residualLatest,
                latestPerception);

            // ---------------------------------------------
            // 6. Update dashboard-level hover data
            // ---------------------------------------------
            latestCrimeHoverData = crimeLatest;
            latestResidualHoverData = residualLatest;
            latestHeadlineHoverData = headlineLatest;
            latestPerceptionHoverData = latestPerception;

            // ---------------------------------------------
            // 7. Latest date (use crime latest date)
            // ---------------------------------------------
            latestDate = d3.max(
                Array.from(activeCrimeTypes).map(type => {
                    const arr = crimeDataByType.get(type);
                    return arr && arr.length ? arr[arr.length - 1].date : null;
                })
            );

            // ---------------------------------------------
            // 8. Update hoverList
            // ---------------------------------------------
            updateHoverList(latestDate, mergedLatest, true);
        }



        // update the hoverlist
        function updateHoverList(date, mergedData = [], showDate = true) {
            const hoverListContainer = d3.select("#hoverList");

            // Always re-read the selected metric label (cheap)
            selectedMetric = d3.select("#perception-metric-label").text();
            // selectedMetric = d3.select("#crime-type-label").text();

            // If no crime types active → clear hoverlist and hide
            if (activeCrimeTypes.size === 0) {
                hoverListContainer.selectAll(".hover-row").remove();
                hoverListContainer.style("display", "block");
                // clear dashboard-level latest values
                latestCrimeHoverData = [];
                latestHeadlineHoverData = [];
                latestResidualHoverData = [];
                latestPerceptionHoverData = null;
                latestDate = null;
                return;
            }

            // Ensure hoverlist visible
            hoverListContainer.style("display", "block").style("opacity", 1);

            // Filter mergedData to only active crime types
            const filteredRows = (mergedData || []).filter(d => activeCrimeTypes.has(d.crime_type));
            // compute residual extent for centered residual bars
            const residualExtent = d3.extent(filteredRows, d => (d.residual == null ? 0 : d.residual));

            // call the renderer
            renderHoverList(filteredRows, {
                containerSelector: "#hover-list-rows",   // ensure you added <ul id="hover-list-rows"> under #hoverList
                colorScale: typeof crimeColor !== "undefined" ? crimeColor : null,
                maxHeadlines: d3.max(filteredRows, d => d.headline) ?? 1,
                maxCrime: d3.max(filteredRows, d => d.crime) ?? 1,
                residualExtent
            });

            // Update dashboard-level latest hover data so other UI can consume it (same shape as before)
            latestCrimeHoverData = filteredRows.map(d => ({ crime_type: d.crime_type, crime: d.crime ?? null }));
            latestHeadlineHoverData = filteredRows.map(d => ({ crime_type: d.crime_type, headline: d.headline ?? null }));
            latestResidualHoverData = filteredRows.map(d => ({ crime_type: d.crime_type, residual: d.residual ?? null }));
            latestPerceptionHoverData = (filteredRows.length && filteredRows[0].perception != null)
                ? filteredRows[0].perception
                : null;

            // preserve latestDate behavior
            if (date) latestDate = date;

        }



        ///////////////////////////////////////////////////////////////////////
        // INCLUDE HIGHLIGHT LOGIC
        ///////////////////////////////////////////////////////////////////////

        // ONLY PLACE WHERE HOVER STATE CHANGES
        function setHoverCrimeType(crimeTypeName) {
            hoverCrimeType = crimeTypeName;
            updateDashboardHoverState();
        }

        function setHoverDate(q) {
            hoverDate = q;
            updateDashboardHoverState();
        }

        function onHeatmapHoverCell(crimeType, date) {
            // Guard: require a date
            if (!date) return;

            // Helper: snap a Date down to the quarter start (Jan/Apr/Jul/Oct)
            function snapToQuarter(d) {
                const month = d.getMonth();
                const quarterStartMonth = month < 3 ? 0 : month < 6 ? 3 : month < 9 ? 6 : 9;
                return new Date(d.getFullYear(), quarterStartMonth, 1);
            }

            // 1. Set hover state FIRST (monthly date for heatmap)
            hoverCrimeType = crimeType;
            hoverDate = date;

            // If your dashboard expects setHoverCrimeType/setHoverDate callbacks, call them
            if (typeof setHoverCrimeType === "function") setHoverCrimeType(crimeType);
            if (typeof setHoverDate === "function") setHoverDate(date);
            // If those callbacks do not call updateDashboardHoverState, call it here
            if (typeof updateDashboardHoverState === "function") updateDashboardHoverState();

            // 2. VISUAL heatmap highlight (row + column + cell)
            heatmapModule.highlightCell(crimeType, date);

            // 3. Build residual hover data (monthly) aligned with activeCrimeTypes
            const headlineField = useDuplicates ? "total_duplicate_headline_count" : "total_headline_count";
            const headlineHoverData = Array.from(activeCrimeTypes).map(type => {
                const arr = headlineDataByType.get(type);
                const row = arr?.find(d => d.date.getTime() === date.getTime());
                return { crime_type: type, headline_count: row ? row[headlineField] : null };
            });

            // 4. Build crime hover data (monthly)
            const crimeHoverData = Array.from(activeCrimeTypes).map(b => {
                const arr = crimeDataByType.get(b);
                const row = arr?.find(d => d.date && d.date.getTime() === date.getTime());
                return { crime_type: b, crime: row ? row.crime_count : null };
            });

            // 5. Perception: snap to quarter and read single aggregated value for that quarter
            const snappedQuarterDate = snapToQuarter(date);

            // Prefer percDataByDate Map keyed by timestamp; fallback to aggregatedPerception array
            // let percHoverValue = null;
            // if (typeof percDataByDate !== "undefined" && percDataByDate && percDataByDate.size) {
            //     percHoverValue = percDataByDate.get(snappedQuarterDate.getTime()) ?? null;
            // } else if (Array.isArray(aggregatedPerception) && aggregatedPerception.length) {
            //     const pRow = aggregatedPerception.find(p => p.date && p.date.getTime() === snappedQuarterDate.getTime());
            //     percHoverValue = pRow ? pRow.avg : null;
            // }

            let percHoverValue = null;
            const metricMap = percDataByDate.get(selectedMetric); // percDataByDate is Map(metric -> Map)
            if (metricMap) {
                percHoverValue = metricMap.get(snappedQuarterDate.getTime()) ?? null;
            } else {
                // fallback: if you still have an aggregatedPerception object, try to find the row
                const arr = aggregatedPerception[selectedMetric] || [];
                const pRow = arr.find(p => p.date && p.date.getTime() === snappedQuarterDate.getTime());
                percHoverValue = pRow ? pRow.avg : null;
            }

            // 3. Build residual hover data (monthly) aligned with activeCrimeTypes
            const residualHoverData = Array.from(activeCrimeTypes).map(b => {
                const arr = residualDataByCrimeType.get(b);
                const row = arr?.find(d => d.date && d.date.getTime() === snappedQuarterDate.getTime());
                return { crime_type: b, residual: row ? row.residual : null };
            });

            // 6. Merge using your existing helper (crimeArr, residualArr, perceptionValue)
            const mergedHoverData = mergeCrimeHeadlineResidual(
                headlineHoverData,
                crimeHoverData,
                residualHoverData,
                percHoverValue
            );

            // 7. Update dashboard-level hover data
            latestResidualHoverData = residualHoverData;
            latestCrimeHoverData = crimeHoverData;
            latestPerceptionHoverData = percHoverValue;

            // 8. Update hover list
            updateHoverList(date, mergedHoverData, true);

            // 9. Move hoverlines (monthly position)
            const snappedX = x(date);
            hoverLineResidual.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
            hoverLineCrime.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
            hoverLinePerc.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);

            // Ensure hover lines are on top
            hoverLineResidual.raise();
            hoverLineCrime.raise();
            hoverLinePerc.raise();
        }
        // ---------- Format helpers ----------
        const fmtInt = v => v == null ? "–" : d3.format(",")(v);
        const fmtPct = v => v == null ? "–" : `${(+v).toFixed(1)}%`;
        const fmtResidual = v => v == null ? "–" : (+v).toFixed(2);

// ---------- drawMicroBars (draws into a metric container node) ----------
        function drawMicroBarsForRow(rowNode, item, scales, colorScale) {
            // rowNode: DOM element for the row
            // item: { crime_type, headline, crime, perception, residual }
            // scales: { headline, crime, perception, residual, width }
            const w = scales.width || 80;
            // HEADLINE
            const svgH = rowNode.querySelector(".metric.headline svg");
            svgH && (svgH.innerHTML = "");
            if (svgH) {
                if (item.headline == null) {
                    svgH.insertAdjacentHTML("beforeend", `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    const width = Math.max(1, scales.headline(Math.min(item.headline, scales.headlineCap)));
                    svgH.insertAdjacentHTML("beforeend", `<rect x="0" y="2" width="${width}" height="8" fill="${colorScale ? colorScale(item.crime_type) : '#888'}" rx="2"></rect>`);
                }
            }

            // CRIME
            const svgC = rowNode.querySelector(".metric.crime svg");
            svgC && (svgC.innerHTML = "");
            if (svgC) {
                if (item.crime == null) {
                    svgC.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    const width = Math.max(1, scales.crime(Math.min(item.crime, scales.crimeCap)));
                    svgC.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${width}" height="8" fill="${colorScale ? colorScale(item.crime_type) : '#666'}" rx="2"></rect>`);
                }
            }

            // PERCEPTION
            const svgP = rowNode.querySelector(".metric.perception svg");
            svgP && (svgP.innerHTML = "");
            if (svgP) {
                if (item.perception == null) {
                    svgP.insertAdjacentHTML("beforeend", `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    const width = scales.perception(Math.max(0, Math.min(100, item.perception)));
                    svgP.insertAdjacentHTML("beforeend", `<rect x="0" y="2" width="${width}" height="8" fill="${colorScale ? colorScale(item.crime_type) : '#4a90e2'}" rx="2"></rect>`);
                }
            }

            // RESIDUAL (centered)
            const svgR = rowNode.querySelector(".metric.residual svg");
            if (svgR) {
                svgR.innerHTML = "";

                // fixed zero position in the center
                const zeroX = w / 2;

                // center tick
                svgR.insertAdjacentHTML("beforeend",
                    `<line x1="${zeroX}" x2="${zeroX}" y1="1" y2="11" stroke="rgba(0,0,0,0.12)" stroke-width="1"></line>`);

                if (item.residual == null || isNaN(item.residual)) {
                    svgR.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    // assume residuals are normalized to [-1, 1]; clamp to avoid overflow
                    const r = Math.max(-1, Math.min(1, +item.residual));

                    // compute pixel position for the value relative to center
                    const valX = zeroX + r * (w / 2);

                    if (r < 0) {
                        // negative: draw from valX (left of center) to center, red
                        const rectX = valX;
                        const rectW = Math.max(0, zeroX - valX);
                        svgR.insertAdjacentHTML("beforeend",
                            `<rect x="${rectX}" y="2" width="${rectW}" height="8" fill="#931010" rx="2"></rect>`);
                    } else if (r > 0) {
                        // positive: draw from center to valX, green
                        const rectX = zeroX;
                        const rectW = Math.max(0, valX - zeroX);
                        svgR.insertAdjacentHTML("beforeend",
                            `<rect x="${rectX}" y="2" width="${rectW}" height="8" fill="#165007" rx="2"></rect>`);
                    } else {
                        // exactly zero: optionally draw a tiny marker so users see a value
                        svgR.insertAdjacentHTML("beforeend",
                            `<rect x="${zeroX - 1}" y="2" width="2" height="8" fill="rgba(0,0,0,0.12)" rx="1"></rect>`);
                    }
                }
            }

        }

// ---------- render Hover List (main renderer) ----------
        /*
          mergedArray: array of items { crime_type, crime, headline, residual, perception }
          options: { containerSelector, colorScale, maxHeadlines, maxCrime, residualExtent }
        */
        function renderHoverList(mergedArray, options = {}) {
            const containerSelector = options.containerSelector || "#hover-list-rows";
            let container = document.querySelector(containerSelector);
            if (!container) {
                // fallback: append a UL inside #hoverList if not present
                const parent = document.getElementById("hoverList");
                container = document.createElement("ul");
                container.id = "hover-list-rows";
                container.style.margin = 0;
                container.style.padding = 0;
                parent.appendChild(container);
            }

            const colorScale = options.colorScale || null;
            const w = 80;
            const scales = {
                width: w,
                headline: d3.scaleLinear().domain([0, Math.max(1, options.maxHeadlines || 1)]).range([0, w]),
                headlineCap: Math.max(1, options.maxHeadlines || 1),
                crime: d3.scaleLinear().domain([0, Math.max(1, options.maxCrime || 1)]).range([0, w]),
                crimeCap: Math.max(1, options.maxCrime || 1),
                perception: d3.scaleLinear().domain([0, 100]).range([0, w]),
                residual: d3.scaleLinear().domain(options.residualExtent || d3.extent(mergedArray, d => d.residual) || [-1,1]).range([0, w])
            };

            // reuse nodes
            const existing = new Map();
            container.querySelectorAll(".hover-row").forEach(n => existing.set(n.dataset.crime, n));

            const fragment = document.createDocumentFragment();

            mergedArray.forEach(item => {
                const key = item.crime_type;
                let row = existing.get(key);
                if (!row) {
                    row = document.createElement("li");
                    row.className = "hover-row";
                    row.dataset.crime = key;
                    row.setAttribute("role", "listitem");
                    row.tabIndex = 0;
                    row.innerHTML = `
              <div class="row-left">
                <span class="swatch" aria-hidden="true"></span>
                <span class="crime-name"></span>
              </div>
              <div class="row-values" role="group" aria-label="">
                <div class="metric headline"><svg width="${w}" height="12"></svg><div class="num headline-num"></div></div>
                <div class="metric crime"><svg width="${w}" height="12"></svg><div class="num crime-num"></div></div>
                <div class="metric perception"><svg width="${w}" height="12"></svg><div class="num perception-num"></div></div>
                <div class="metric residual"><svg width="${w}" height="12"></svg><div class="num residual-num"></div></div>
              </div>
            `;

                    // interactions: hover and click call your existing handlers
                    row.addEventListener("mouseenter", () => {
                        if (typeof setHoverCrimeType === "function") setHoverCrimeType(key);
                        if (typeof highlightLine === "function") highlightLine(key);
                    });
                    row.addEventListener("mouseleave", () => {
                        if (typeof setHoverCrimeType === "function") setHoverCrimeType(null);
                        if (typeof clearHoverHighlight === "function") clearHoverHighlight();
                    });
                    row.addEventListener("click", () => {
                        // if (typeof toggleActiveCrimeTypes === "function") toggleActiveCrimeTypes(key);
                    });
                }
                d3.select(row).datum(item);


                // populate left
                row.querySelector(".crime-name").textContent = key;
                const sw = row.querySelector(".swatch");
                if (colorScale) sw.style.background = colorScale(key);
                else sw.style.background = "#999";

                // populate numbers
                row.querySelector(".headline-num").textContent = fmtInt(item.headline);
                row.querySelector(".crime-num").textContent = fmtInt(item.crime);
                row.querySelector(".perception-num").textContent = fmtPct(item.perception);
                row.querySelector(".residual-num").textContent = fmtResidual(item.residual);

                // set aria label
                const aria = `${key}: Headlines ${item.headline == null ? "missing" : fmtInt(item.headline)}, Crime ${item.crime == null ? "missing" : fmtInt(item.crime)}, Perception ${item.perception == null ? "missing" : fmtPct(item.perception)}, Residual ${item.residual == null ? "missing" : fmtResidual(item.residual)}`;
                row.querySelector(".row-values").setAttribute("aria-label", aria);

                // draw micro bars
                drawMicroBarsForRow(row, item, scales, colorScale);

                fragment.appendChild(row);
                existing.delete(key);
            });

            // remove leftover nodes
            existing.forEach(n => n.remove());

            container.appendChild(fragment);
        }


        function setupTrendToggle() {
            const btn = document.getElementById("toggleTrendBtn");
            const headlineChart = document.getElementById("headlines-title");
            const headlineTitle = document.getElementById("headline-chart");
            const crimeChart = document.getElementById("chart-crime");
            const perceptionChart = document.getElementById("chart-perception");
            const crimeTitle = document.getElementById("crime-title");
            const perceptionTitle = document.getElementById("perception-title");
            const residualChart = document.getElementById("chart-residual");
            const residualTitle = document.getElementById("residual-title");

            if (!btn) return;

            const show = el => {
                if (!el) return;
                el.classList.remove("hidden-chart");
                el.classList.add("visible-chart");
                el.setAttribute("aria-hidden", "false");
            };
            const hide = el => {
                if (!el) return;
                el.classList.remove("visible-chart");
                el.classList.add("hidden-chart");
                el.setAttribute("aria-hidden", "true");
            };

            // Ensure primary elements are visible
            show(headlineChart);
            show(headlineTitle);
            show(crimeChart);
            show(perceptionChart);
            show(crimeTitle);
            show(perceptionTitle);

            // Initial state: residual chart VISIBLE
            let residualVisible = true;
            show(residualChart);
            show(residualTitle);

            // Button initial label
            btn.textContent = residualVisible ? "Hide Residual Chart" : "Show Residual Chart";

            btn.addEventListener("click", () => {
                residualVisible = !residualVisible;

                if (residualVisible) {
                    btn.textContent = "Hide Residual Chart";
                    show(residualChart);
                    show(residualTitle);
                } else {
                    btn.textContent = "Show Residual Chart";
                    hide(residualChart);
                    hide(residualTitle);
                }

                // Emit event for other modules to react (optional)
                try {
                    const ev = new CustomEvent("residualToggle", { detail: { visible: residualVisible } });
                    document.dispatchEvent(ev);
                } catch (e) {
                    // ignore if CustomEvent not supported
                }
            });
        }

        setupTrendToggle();


        function updateDashboardActiveState() {
            crimeChart.initializeCrimeChart();
            headlineChart.initializeHeadlineChart();
            perceptionChart.initializePerceptionChart(selectedMetric);

            // After you create/initialize charts (immediately after headlineChart, crimeChart, residualChart are created)
            highlightLine = (crimeType) => {
                // call whichever chart exposes the method; guard with typeof
                if (headlineChart && typeof headlineChart.highlightLine === "function") headlineChart.highlightLine(crimeType);
                if (crimeChart && typeof crimeChart.highlightLine === "function") crimeChart.highlightLine(crimeType);
                if (residualChart && typeof residualChart.highlightLine === "function") residualChart.highlightLine(crimeType);
            };

            clearHoverHighlight = () => {
                if (headlineChart && typeof headlineChart.clearHoverHighlight === "function") headlineChart.clearHoverHighlight();
                if (crimeChart && typeof crimeChart.clearHoverHighlight === "function") crimeChart.clearHoverHighlight();
                if (residualChart && typeof residualChart.clearHoverHighlight === "function") residualChart.clearHoverHighlight();
            };
            setHoverCrimeType = (crimeType) => {
                hoverCrimeType = crimeType;
                // keep existing behavior
                updateDashboardHoverState();
                // optionally also call chart-level hover setters if they exist
                if (headlineChart && typeof headlineChart.setHoverCrimeType === "function") headlineChart.setHoverCrimeType(crimeType);
                if (crimeChart && typeof crimeChart.setHoverCrimeType === "function") crimeChart.setHoverCrimeType(crimeType);
                if (residualChart && typeof residualChart.setHoverCrimeType === "function") residualChart.setHoverCrimeType(crimeType);
            };
            crimeChart.updateActiveCrimeTypes(activeCrimeTypes);
            headlineChart.updateActiveCrimeTypes(activeCrimeTypes)
            residualChart.updateActiveCrimeTypes(activeCrimeTypes);
            chordChart.updateActiveCrimeTypes(activeCrimeTypes);
            heatmapModule.updateActiveCrimeTypes(activeCrimeTypes);


            // chordChart.updateChordChart(activeCrimeTypes);

            // 3. Dim charts if nothing active
            const nothingActive = activeCrimeTypes.size === 0;
            if (crimeChart && typeof crimeChart.dim === "function") crimeChart.dim(nothingActive);
            if (residualChart && typeof residualChart.dim === "function") residualChart.dim(nothingActive);
            if (headlineChart && typeof headlineChart.dim === "function") headlineChart.dim(nothingActive);
            // remake this:
            showLatestValues(true);
        }

        // This is the central hover controller.
        // Every module calls setHoverCrimeType() on hover.
        function updateDashboardHoverState() {

            const hoverListSel = d3.select("#hoverList");

            // --------------------------------------------------
            // Helper: apply and clear cross-chart highlights
            // --------------------------------------------------
            function applyHoverHighlights(type) {
                // HoverList highlight
                hoverListSel.selectAll(".hover-row")
                    .classed("selected-hover-row", r => r.crime_type === selectedHoverRow)
                    .classed("hover-highlight-row", r =>
                        type &&
                        r.crime_type === type &&
                        r.crime_type !== selectedHoverRow
                    );

                crimeChart.highlightLine(type);
                residualChart.highlightLine(type);
                headlineChart.highlightLine(type);
                // perceptionChart.highlightLine(type); // enable if you have perceptionChart

                // Chord chart highlight
                if (typeof chordChart !== "undefined" && chordChart.highlightGroup) {
                    chordChart.highlightGroup(type);
                }

                // Ensure hover lines are on top
                hoverLineCrime.raise();
                hoverLinePerc && hoverLinePerc.raise();
                hoverLineResidual.raise();
                hoverLineHeadline.raise();
            }

            function clearAllHighlights() {
                // HoverList
                hoverListSel.selectAll(".hover-row")
                    .classed("selected-hover-row", false)
                    .classed("hover-highlight-row", false);

                // Line charts
                crimeChart.clearHoverHighlight();
                residualChart.clearHoverHighlight();
                headlineChart.clearHoverHighlight();
                // perceptionChart.clearHoverHighlight();

                // Chord chart
                if (typeof chordChart !== "undefined" && chordChart.clearHighlight) {
                    chordChart.clearHighlight();
                }

                // Heatmap
                heatmapModule.clearHoverHighlight();
                heatmapModule.clearCellHover();

                // Hide hover lines
                hoverLineCrime.style("opacity", 0);
                hoverLinePerc && hoverLinePerc.style("opacity", 0);
                hoverLineResidual.style("opacity", 0);
                hoverLineHeadline.style("opacity", 0);
            }

            // --------------------------------------------------
            // 0. Determine the date to display
            // --------------------------------------------------
            const displayDate = hoverDate ? hoverDate : latestDate;
            const monthYear = displayDate ? d3.timeFormat("%B %Y")(displayDate) : "";

            // --------------------------------------------------
            // 1. HoverList row highlight
            // --------------------------------------------------
            if (hoverCrimeType && activeCrimeTypes.size > 0) {
                hoverListSel.selectAll(".hover-row")
                    .classed("selected-hover-row", r => r.crime_type === selectedHoverRow)
                    .classed("hover-highlight-row", r =>
                        hoverCrimeType &&
                        r.crime_type === hoverCrimeType &&
                        r.crime_type !== selectedHoverRow
                    );
            } else {
                hoverListSel.selectAll(".hover-row")
                    .classed("selected-hover-row", false);
            }

            // --------------------------------------------------
            // 2. Line chart hover highlight (centralized)
            // --------------------------------------------------
            const highlightType = hoverCrimeType || selectedHoverRow;

            if (highlightType) {
                applyHoverHighlights(highlightType);
            } else {
                clearAllHighlights();
            }

            // --------------------------------------------------
            // 3. Heatmap hover highlight (also drive cross-chart highlights)
            // --------------------------------------------------
            // If heatmap has both date and crime hover (cell hover), highlight that cell and also highlight the crime type across charts
            if (hoverDate && hoverCrimeType) {
                heatmapModule.highlightCell(hoverCrimeType, hoverDate);
                // also ensure other charts reflect the hover
                applyHoverHighlights(hoverCrimeType);
            } else if (hoverDate && !hoverCrimeType) {
                // highlight column only
                heatmapModule.highlightCell(null, hoverDate);
                // keep other highlights as-is (selectedHoverRow may still apply)
                if (selectedHoverRow) applyHoverHighlights(selectedHoverRow);
            } else if (hoverCrimeType && !hoverDate) {
                // row hover: highlight row and propagate to other charts
                heatmapModule.highlightRow(hoverCrimeType);
                applyHoverHighlights(hoverCrimeType);
            } else {
                // no heatmap hover: clear heatmap-specific highlights but keep selectedHoverRow if present
                heatmapModule.clearHoverHighlight();
                heatmapModule.clearCellHover();
                if (selectedHoverRow) {
                    applyHoverHighlights(selectedHoverRow);
                } else {
                    // nothing selected or hovered
                    if (!highlightType) clearAllHighlights();
                }
            }

            // --------------------------------------------------
            // 5. Hoverlist title (depends on active crime types AND hoverDate)
            // --------------------------------------------------
            if (activeCrimeTypes.size === 0) {
                d3.select("#hover-list-title")
                    .html(`Select Crime Types <br> To See a Summary of Selected Crime Categories`);
            } else if (hoverDate) {
                d3.select("#hover-list-title")
                    .html(`Showing Crime and Perception Info for<br>
                   <strong style="font-size:1.2em;">${monthYear}</strong>`);
            } else {
                d3.select("#hover-list-title")
                    .html(`Showing Latest Crime and Perception Info for<br>
                   <strong style="font-size:1.2em;">${monthYear}</strong>`);
            }

            // --------------------------------------------------
            // 6. Hoverline movement
            // --------------------------------------------------
            if (hoverDate) {
                const snappedX = x(hoverDate);
                hoverLineCrime.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
                hoverLinePerc && hoverLinePerc.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
                hoverLineResidual.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
                hoverLineHeadline.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);

                hoverLineCrime.raise();
                hoverLinePerc && hoverLinePerc.raise();
                hoverLineResidual.raise();
                hoverLineHeadline.raise();
            } else {
                hoverLineCrime.style("opacity", 0);
                hoverLinePerc && hoverLinePerc.style("opacity", 0);
                hoverLineResidual.style("opacity", 0);
                hoverLineHeadline.style("opacity", 0);
            }
        }



    }).catch(err => {
        console.error("DATA LOAD ERROR:", err);

    });
}

export default drawDashboard
