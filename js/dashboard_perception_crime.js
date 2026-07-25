// Perception/crime dashboard (no headline data)
import { drawCrimeChart } from "./dash_crime_linechart.js";
import { drawPerceptionChart } from "./dash_perception_linechart.js";
import { drawChoroMap} from "./dash_bivariate_map.js";
import { drawHeatmap } from "./dash_heatmap_crime_perception.js";
import {drawResidualChart} from "./dash_residual_linechart.js";

// import { drawHeatmap } from "./heatmap_crime_perception.js";   // you will create this

export function drawDashboard() {

    // CONTAINERS
    const residualContainer = "#chart-residual"
    const crimeContainer = "#chart-crime";
    const perceptionContainer = "#chart-perception";
    const hoverListContainer = "#hoverList";
    const choroMapContainer = "#choro-map";
    const heatmapContainer = "#heatmap";

    // SHARED STATES
    let activeBoroughs = new Set();   // persistent selection
    let hoverBorough = null;          // temporary hover variable
    let snappedDate = null;           // shared hover date


    // LATEST HOVER DATA
    let latestResidualHoverData = null;
    let residualData = null;
    let latestCrimeHoverData = null;
    let latestPerceptionHoverData = null;
    let latestDate = null;
    let latestMapHoverData = null;
    let selectedHoverRow = null;     // pinned borough
    let hoverQuarter = null;        // Date object snapped to quarter
    let hoverDateDisplay = null;   // formatted string: "January 2021"


    // DATA VISUAL MODULES
    let residualChart = null;
    let crimeChart = null;
    let perceptionChart = null;
    let choroMap = null;
    let heatmapModule = null;
    let hoverListIsHovering = false;



    // DEFAULT SELECTED METRIC
    let selectedMetric = "Good job"

    function preprocessResiduals(data) {
        data.forEach(d => {
            // Parse date
            d.date = new Date(d.date);
            // Only trim borough if it exists
            if (d.borough != null && d.borough !== "") {
                d.borough = d.borough.trim();
            }
            // Convert all residual columns to numbers
            for (const key of Object.keys(d)) {
                if (key.endsWith("_residual")) {
                    d[key] = +d[key];
                }
            }
        });
    }

    function preprocessCrime(crimeData) {
        const parseDate = d3.timeParse("%m/%d/%Y");
        crimeData.forEach(d => {
            d.date = parseDate(d.date);
            d.crime_count = +d.crime_count;
            d.borough = d.borough.trim();
        });
    }

    function preprocessPerception(perceptionData) {
        perceptionData.forEach(d => {
            d.date = new Date(d.date);
            d.metric_value = +d.metric_value;        // convert string → number
            d.metric_value_pct = d.metric_value * 100; // convert decimal → percent
            d.borough = d.borough.trim();
            d.metric = d.metric.trim();
        });
    }

    function preprocessMapData(mapData) {
        mapData.forEach(d => {
            d.borough = d.borough.trim();
            d.crime_bin = d.crime_bin.trim();
            d.perc_bin = d.perc_bin.trim();
            d.color = d.color.trim();
            d.metric = d.metric.trim();
            d.date = new Date(d.date); //parse date so it matches hoverQuarter
        });
    }

    function preprocessHeatmapData(heatmapData) {
        heatmapData.forEach(d => {
            // Parse date
            d.date = new Date(d.date);

            // Normalize quarter format: "Q2_2122" → "2021-Q2"
            const [qPart, fyPart] = d.quarter.split("_");   // ["Q2", "2122"]

            const quarterNumber = +qPart.replace("Q", "");  // 2

            // Fiscal year "2122" means FY 2021–2022 → quarter belongs to 2021
            const fiscalYearStart = +fyPart - 1;            // 2122 → 2021

            d.quarter_norm = `${fiscalYearStart}-Q${quarterNumber}`;

            // Clean borough + metric
            d.borough = d.borough.trim();
            d.metric = d.metric.trim();

            // Convert numbers
            d.crime_count = +d.crime_count;
            d.perception_value = +d.perception_value;
            d.hybrid_sjsd = +d.hybrid_sjsd;
        });
    }

    // Load BOTH datasets in parallel
    Promise.all([
        d3.csv("../data/aggregated_residuals_wide.csv"),      // 0
        d3.csv("../data/borough_residuals_wide.csv"),         // 1
        d3.csv("../data/crime_borough_monthly.csv"),          // 2
        d3.csv("../data/MOPAC_FULL_LONG_Public_Perception.csv"), // 3
        d3.json("../data/london-boroughs.json"),              // 4
        d3.csv("../data/FULL_crime_perception_bins_colors.csv"), // 5
        d3.csv("../data/s-jsd_hybrid_heatmap_perception_crime.csv") // 6
    ]).then(([aggregatedResiduals, boroughResiduals, crimeData, perceptionData, topoJSON, mapData, heatmapData]) => {
        console.log("Data loaded:",
            crimeData.length,
            perceptionData.length,
            mapData.length,
            boroughResiduals.length,
            aggregatedResiduals.length
        );

        preprocessResiduals(boroughResiduals);
        preprocessResiduals(aggregatedResiduals);
        preprocessCrime(crimeData);
        preprocessPerception(perceptionData);
        preprocessMapData(mapData);
        preprocessHeatmapData(heatmapData);

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

        // BUILD RESIDUAL SCALES BASED ON AGGREGATE AND BOROUGH RESIDUALS!
        const aggregatedResidualData = aggregatedResiduals
            .filter(d => d.date >= cutoff)
            .sort((a, b) => a.date - b.date)
            .map(d => ({
                date: d.date,
                residual: d[selectedMetric.replace(" ", "_") + "_residual"]
            }))
            .filter(d => d.residual != null && !isNaN(d.residual));

        const boroughResidualData = boroughResiduals
            .filter(d => d.date >= cutoff)
            .sort((a, b) => a.date - b.date)
            .map(d => ({
                borough: d.borough,
                date: d.date,
                residual: d[selectedMetric.replace(" ", "_") + "_residual"]
            }))
            .filter(d => d.residual != null && !isNaN(d.residual));


        // for residual calculations
        const allResiduals = aggregatedResidualData.concat(boroughResidualData);

        const minResidual = d3.min(allResiduals, d => d.residual);
        const maxResidual = d3.max(allResiduals, d => d.residual);

        // Residual y-scale
        const yResidual = d3.scaleLinear()
            .domain([minResidual, maxResidual])
            .range([innerHeight, 0])
            .nice();

        // zoom logic tbd
        const resetZoomBtn = document.getElementById("resetZoomBtn");
        resetZoomBtn.addEventListener("click", () => {
            hasZoomed = false;
            resetZoomBtn.style.display = "none";
            applyXDomain(fullXDomain);
            // reset summary pills after resetting zoom
            updateSummaryPills();
        });

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

        const palette = generateBoroughPalette(32);
        // then use palette (array of hex strings)
        // const colorScale = d3.scaleOrdinal().domain(boroughNames).range(palette);

        const crimeColor = d3.scaleOrdinal(palette);
        const perceptionColor = d3.scaleOrdinal(palette);
        // const residualColor = d3.scaleOrdinal(d3.schemeTableau10);

        //////////////////////////////
        // POPULATE METRIC DROPDOWN //
        //////////////////////////////
        const perceptionMetrics = Array.from(
            new Set(perceptionData.map(d => d.metric.trim()))
        );

        const dropdown = d3.select("#perception-metric-container");
        const trigger  = d3.select("#perception-metric-trigger");
        const label    = d3.select("#perception-metric-label");
        const menu     = d3.select("#perception-metric-menu");

        selectedMetric = perceptionMetrics[0];
        label.text(selectedMetric);

        // build menu items listener events
        const items = menu.selectAll(".glass-dropdown-item")
            .data(perceptionMetrics)
            .enter()
            .append("button")
            .attr("class", d =>
                "glass-dropdown-item" + (d === selectedMetric ? " is-active" : "")
            )
            .text(d => d)
            .on("click", (event, d) => {
                selectedMetric = d;
                label.text(d);

                // update active state
                items.classed("is-active", item => item === d);

                // close dropdown
                dropdown.classed("is-open", false);

                // call your existing update function
                updatePerceptionMetric();
                // update the summary pills after updating metric
                // only the perception pill average % should change
                updateSummaryPills();
            });

        // toggle open/close
        trigger.on("click", () => {
            const isOpen = dropdown.classed("is-open");
            dropdown.classed("is-open", !isOpen);
        });

        // ⭐ Build residualData for selected metric
        let residualData = boroughResiduals.map(d => ({
            borough: d.borough,
            date: d.date,
            residual: d[selectedMetric.replace(" ", "_") + "_residual"]
        }));

        //set the latest values: (WILL CHANGE LATER WHEN SNAPPING FUNCTIONALITY IS INTRODUCED)
        latestResidualHoverData = null;
        latestCrimeHoverData = null;
        latestPerceptionHoverData = null;
        // latestCrimeHoverData = crimeData.filter(d => d.date.getTime() === snappedDate?.getTime());
        // latestPerceptionHoverData = perceptionData.filter(d => d.date.getTime() === snappedDate?.getTime());
        latestMapHoverData = mapData; // map is not time‑dependent
        // ===============================
        // INITIALIZE MODULES
        // ===============================

        // Draw charts
        residualChart = drawResidualChart({
            container: residualContainer,
            aggregatedResiduals: aggregatedResidualData,   // ONE LINE
            boroughResiduals: boroughResidualData,      // MANY LINES
            x,
            y: yResidual,
            width,
            height,
            margin,
            color: crimeColor,
            activeBoroughs,
            setHoverBorough,
            onLineClick: toggleActiveBorough,
            onZoom: onZoom
        });

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
            activeBoroughs,
            setHoverBorough,
            onLineClick: toggleActiveBorough,
            onZoom: onZoom
            // applyXd
        });

        perceptionChart = drawPerceptionChart({
            container: perceptionContainer,
            data: perceptionData,
            x,
            y: yPerception,
            width,
            height,
            margin,
            color: perceptionColor,
            activeBoroughs,
            setHoverBorough,
            onLineClick: toggleActiveBorough,
            onZoom: onZoom
        });

        heatmapModule = drawHeatmap({
            container: "#heatmap",
            data: heatmapData,
            selectedMetric,
            activeBoroughs,
            setHoverBorough,
            setHoverQuarter,
            onClick: toggleActiveBorough,
            onHeatmapHoverCell,
            updateDashboardHoverState
            // onHeatmapHover,
        });

        // Filter map data for initial metric
        let filteredMapData = mapData.filter(d => d.metric === selectedMetric);
        residualChart.initializeResidualChart();
        perceptionChart.initializePerceptionChart(selectedMetric);
        crimeChart.initializeCrimeChart();


        // d3.select(choroMapContainer).select("*").remove();

        // Draw initial map
        choroMap = drawChoroMap({
            container: choroMapContainer,
            topoJSON,
            data: filteredMapData,
            setHoverBorough,
            onClick: toggleActiveBorough,
            selectedMetric
        });

        ///////////////////////////////////////////////////////////////////////
        // HOVERLINE LOGIC + LISTENERS
        ///////////////////////////////////////////////////////////////////////
        // Initialize hoverList with instructional title


        // Variables for the hoverLine and hoverlist
        residualData.sort((a, b) => a.date - b.date); // ensure data is sorted by date
        const residualDataByBorough = d3.group(residualData, d => d.borough);
        const crimeDataByBorough = d3.group(crimeData, d => d.borough);
        const percDataByBorough = d3.group(perceptionData, d => d.borough);
        const plotGroupNode = residualChart.plotGroupNode;

        // const plotGroupNode = crimeChart.plotGroupNode;
        const lineChartsNode = document.querySelector("#line-charts");


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


        showLatestValues(true)
        updateHoverList(null, [], null);
        updateDashboardHoverState();
        // UPDATES THE HOVERLINE LISTENER
        lineChartsNode.addEventListener("mousemove", event => {
            // if no boroughs active, don't do anything
            if (activeBoroughs.size === 0) return;
            if (!residualDataByBorough.size) return;

            //NOTE that the coordinate reference is based on the x position of the chart axis'
            const [mx] = d3.pointer(event, plotGroupNode);
            const rawDate = x.invert(mx);
            // 4. Snap to nearest CRIME date (monthly)
            let snappedCrimeDate = rawDate;
            // Find first active borough with crime data
            const firstCrimeActive = Array.from(activeBoroughs)
                .map(b => crimeDataByBorough.get(b))
                .find(arr => arr && arr.length > 0);

            if (firstCrimeActive) {
                const closestCrime = firstCrimeActive.reduce((a, c) =>
                    Math.abs(c.date - rawDate) < Math.abs(a.date - rawDate) ? c : a
                );
                snappedCrimeDate = closestCrime.date;
            }

            // 5. Snap perception date DOWN to nearest quarter
            // Example quarters: Jan, Apr, Jul, Oct
            function snapToQuarter(date) {
                const month = date.getMonth(); // 0–11
                const quarterStartMonth =
                    month < 3 ? 0 :
                        month < 6 ? 3 :
                            month < 9 ? 6 :
                                9;

                return new Date(date.getFullYear(), quarterStartMonth, 1);
            }
            // 6. Move hoverlines using snappedCrimeDate (monthly)
            const snappedPercDate = snapToQuarter(snappedCrimeDate);
            setHoverQuarter(snappedPercDate);
            hoverQuarter = snappedPercDate;
            const snappedX = x(snappedCrimeDate);
            hoverLineResidual
                .attr("x1", snappedX)
                .attr("x2", snappedX)
                .style("opacity", 1)
                .raise();
            hoverLineCrime
                .attr("x1", snappedX)
                .attr("x2", snappedX)
                .style("opacity", 1)
                .raise();
            hoverLinePerc
                .attr("x1", snappedX)
                .attr("x2", snappedX)
                .style("opacity", 1)
                .raise();

            // 7. Build hoverList data for ALL active boroughs
            const snappedResidualDate = snappedPercDate;
            const residualHoverData = Array.from(activeBoroughs).map(borough => {
                const arr = residualDataByBorough.get(borough);
                const row = arr?.find(d => d.date.getTime() === snappedResidualDate.getTime());
                return {
                    borough,
                    residual: row ? row.residual : null
                };
            });

            // Crime values at snappedCrimeDate
            const crimeHoverData = Array.from(activeBoroughs).map(borough => {
                const arr = crimeDataByBorough.get(borough);
                const row = arr?.find(d => d.date.getTime() === snappedCrimeDate.getTime());
                return {
                    borough,
                    crime: row ? row.crime_count : null
                };
            });

            // Perception values at snappedPercDate
            const percHoverData = Array.from(activeBoroughs).map(borough => {
                const arr = percDataByBorough.get(borough);
                const row = arr?.find(d => d.date.getTime() === snappedPercDate.getTime());
                return {
                    borough,
                    perception: row ? row.metric_value_pct : null
                };
            });

            // Merge crime + perception into unified rows
            const mergedHoverData = mergeCrimeAndPerception(residualHoverData, crimeHoverData, percHoverData);

            latestResidualHoverData = residualHoverData;
            latestCrimeHoverData = crimeHoverData;
            latestPerceptionHoverData = percHoverData;
            snappedDate = snappedCrimeDate;

            // 8. Update hoverList
            // compute snappedCrimeDate earlier in handler...
            if (snappedDate && +snappedCrimeDate === +snappedDate) {
                // nothing changed since last frame — skip expensive work
                return;
            }
            snappedDate = snappedCrimeDate;

            updateHoverList(snappedCrimeDate, mergedHoverData, true);
            updateDashboardHoverState();
        });

        lineChartsNode.addEventListener("mouseleave", () => {
            hoverLineCrime.style("opacity", 0);
            hoverLinePerc.style("opacity", 0);
            hoverLineResidual.style("opacity", 0);

            hoverQuarter = null;
            hoverBorough = null;


            if (activeBoroughs.size > 0) {
                showLatestValues(true);
            } else {
                showLatestValues(false);
            }
            updateDashboardHoverState();
        });

        // newwwww
        const heatmapNode = document.querySelector("#heatmap-scroll-wrapper");

        heatmapNode.addEventListener("mouseleave", () => {

            // 1. Clear hover state
            hoverBorough = null;
            hoverQuarter = null;

            // 2. Clear heatmap visual hover
            heatmapModule.clearCellHover();
            heatmapModule.clearHoverHighlight();

            // NEW? MAYBE DELETE
            // 3. Clear hoverlines on ALL charts
            hoverLineCrime.style("opacity", 0);
            hoverLinePerc.style("opacity", 0);
            hoverLineResidual.style("opacity", 0);   // ⭐ REQUIRED

            // 3. Show latest values (if any boroughs selected)
            if (activeBoroughs.size > 0) {
                showLatestValues(true);
            } else {
                showLatestValues(false);
            }

            // 4. Update dashboard titles + choromap + hoverline
            updateDashboardHoverState();
        });



        //merge crime + perception values for the hoverList
        function mergeCrimeAndPerception(residArr, crimeArr, percArr) {
            const out = [];
            for (const r of residArr) {
                const c = crimeArr.find(x => x.borough === r.borough);
                const p = percArr.find(x => x.borough === r.borough);

                out.push({
                    borough: r.borough,
                    residual: r ? (r.residual) : null,
                    crime: c ? c.crime : null,
                    perception: p ? Math.round(p.perception) : null
                });
            }
            // for (const c of crimeArr) {
            //     const p = percArr.find(x => x.borough === c.borough);
            //     const r = residArr.find(x => x.borough === c.borough);
            //
            //     const roundedPerc = p && p.perception != null
            //         ? Math.round(p.perception)
            //         : null;
            //
            //     out.push({
            //         borough: c.borough,
            //         residual: r ? Math.round(r.residual) : null,
            //         crime: c ? c.crime : null,
            //         perception: p ? Math.round(p.perception) : null,
            //     });
            // }

            return out;
        }

        //HOVERLIST per row listeners (hover + click highlight)
        function addHoverRowListeners(selection) {
            selection
                .on("mouseover", (event, d) => {
                    const boroughName = d.borough;
                    // Tell dashboard: user is hovering this borough
                    setHoverBorough(boroughName);
                })

                .on("mouseout", (event, d) => {
                    const boroughName = d.borough;
                    // Only clear hover if this row is not the selected one
                    if (selectedHoverRow !== boroughName) {
                        setHoverBorough(null);
                    }
                })

                .on("click", (event, d) => {
                    const boroughName = d.borough;
                    const wasActive = activeBoroughs.has(boroughName);

                    // Update persistent selection
                    selectedHoverRow = boroughName;

                    // Update hoverList row styling
                    hoverListContainer
                        .selectAll(".hover-row")
                        .classed("selected-hover-row", r => r.borough === boroughName);

                    // Tell dashboard to toggle active borough
                    toggleActiveBorough(boroughName);

                    // Keep hoverlines on top
                    hoverLineCrime.raise();
                    hoverLinePerc.raise();
                    hoverLineResidual.raise();
                });
        }

        ///////////////////////////////////////////////////////////////////////
        // core update functions
        ///////////////////////////////////////////////////////////////////////
        function toggleActiveBorough(boroughName) {
            // Toggle membership
            if (activeBoroughs.has(boroughName)) {
                activeBoroughs.delete(boroughName);
            } else {
                activeBoroughs.add(boroughName);
            }

            // Apply persistent active/dimmed styling
            updateDashboardActiveState();
            // update the summary pills to reflect new active borough
            updateSummaryPills();
        }

        ///////////////////////////////////////////////////////////////////////
        // ZOOM FUNCTIONS
        ///////////////////////////////////////////////////////////////////////
        function applyXDomain(domain) {
            currentXDomain = domain;

            // 1. Update both charts
            residualChart.applyXDomain(domain)

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

            // update the borough lines on the perception chart
            perceptionChart.updateData(filteredPerception);

            // update BOTH charts' x-axis
            residualChart.redrawXAxis();
            crimeChart.redrawXAxis();
            perceptionChart.redrawXAxis();

            //only perception lines need to be redrawn
            // perceptionChart.redrawLines();
            crimeChart.redrawLines();

            // -----------------------------
            // 2. Recompute RESIDUAL DATA (AGG + BOROUGH) (IS THIS NECESSARY TO DO AGAIN?)
            // -----------------------------
            const residualColumn = selectedMetric.replace(" ", "_") + "_residual";

            // Aggregated residuals (already one row per quarter)
            const newAggregatedResiduals = aggregatedResiduals
                .filter(d => d.date >= cutoff)
                .map(d => ({
                    date: d.date,
                    residual: d[residualColumn]
                }))
                .filter(d => d.residual != null && !isNaN(d.residual))
                .sort((a, b) => a.date - b.date);

            // Borough residuals (many lines)
            const newBoroughResiduals = boroughResiduals
                .filter(d => d.date >= cutoff)
                .map(d => ({
                    borough: d.borough,
                    date: d.date,
                    residual: d[residualColumn]
                }))
                .filter(d => d.residual != null && !isNaN(d.residual))
                .sort((a, b) => a.date - b.date);

            // -----------------------------
            // 3. Update RESIDUAL CHART
            // -----------------------------
            residualChart.updateData({
                aggregated: newAggregatedResiduals,
                borough: newBoroughResiduals
            });

            // Preserve active borough styling
            residualChart.updateActiveBoroughs(activeBoroughs);

            // If hovering a quarter, update hoverline position
            if (hoverQuarter) {
                const snappedX = x(hoverQuarter);
                hoverLineResidual
                    .attr("x1", snappedX)
                    .attr("x2", snappedX)
                    .style("opacity", 1)
                    .raise();
            }

            // -----------------------------
            // 4. Update bivariate map
            // -----------------------------
            // Update map
            filteredMapData = mapData.filter(d => d.metric === selectedMetric);
            // Remove old map
            d3.select(choroMapContainer).select("svg").remove();
            // draw new map
            choroMap = drawChoroMap({
                container: choroMapContainer,
                topoJSON,
                data: filteredMapData,
                activeBoroughs,
                setHoverBorough,
                onClick: toggleActiveBorough,
                selectedMetric
            });

            //apply active styling
            // update metric inside map module
            choroMap.updateActiveBoroughs(activeBoroughs);
            choroMap.updateMetric(selectedMetric);

            //update coloring of map when hoverline date changes
            if (hoverQuarter) {
                choroMap.updateMapForQuarter(hoverQuarter);
            }
            // -----------------------------
            // 3. Update heatmap
            // -----------------------------
            if (heatmapModule) {
                heatmapModule.updateMetric(selectedMetric);
            }

            showLatestValues(true);
        }

        // UPDATE PERCEPTION METRIC + SUMMARY PILLS
        // AS SOON AS WINDOW LOADS
        updatePerceptionMetric();
        updateSummaryPills();

        //new
        // function quarterToDate(q) {
        //     if (!q || typeof q !== "string" || !q.includes("-")) {
        //         console.log("date format passed is not right:",q);
        //         return null;   // ⭐ gracefully handle non-quarter hovers
        //     }
        //     const [year, qStr] = q.split("-");
        //     const quarter = +qStr.replace("Q", "");
        //
        //     const month = quarter === 1 ? 0 :
        //         quarter === 2 ? 3 :
        //             quarter === 3 ? 6 :
        //                 9;
        //
        //     return new Date(+year, month, 1);
        // }


        // SUMMARY PILL FUNCTIONS
        function computeCrimeTotal(crimeData, boroughs, dateDomain) {
            const [d0, d1] = dateDomain;

            return crimeData
                .filter(d => boroughs.has(d.borough))
                .filter(d => d.date >= d0 && d.date <= d1)
                .reduce((sum, d) => sum + d.crime_count, 0);
        }

        function computePerceptionAvg(perceptionData, boroughs, dateDomain, selectedMetric) {
            const [d0, d1] = dateDomain;

            const filtered = perceptionData
                .filter(d => d.metric === selectedMetric)
                .filter(d => boroughs.has(d.borough))
                .filter(d => d.date >= d0 && d.date <= d1)
                .map(d => d.metric_value_pct);

            if (filtered.length === 0) return null;

            return d3.mean(filtered);
        }

        function computeCrime12MonthChange(crimeData, boroughs) {

            const latestDate = d3.max(crimeData, d => d.date);
            const oneYearAgo = d3.timeMonth.offset(latestDate, -12);
            const twoYearsAgo = d3.timeMonth.offset(latestDate, -24);

            const currentPeriod = crimeData
                .filter(d => boroughs.has(d.borough))
                .filter(d => d.date > oneYearAgo && d.date <= latestDate)
                .reduce((sum, d) => sum + d.crime_count, 0);

            const previousPeriod = crimeData
                .filter(d => boroughs.has(d.borough))
                .filter(d => d.date > twoYearsAgo && d.date <= oneYearAgo)
                .reduce((sum, d) => sum + d.crime_count, 0);

            if (previousPeriod === 0) return null;

            return ((currentPeriod - previousPeriod) / previousPeriod) * 100;
        }

        function computePerc12MonthChange(perceptionData, boroughs, selectedMetric) {

            const filtered = perceptionData.filter(d => d.metric === selectedMetric);

            const latestDate = d3.max(filtered, d => d.date);
            const oneYearAgo = d3.timeMonth.offset(latestDate, -12);
            const twoYearsAgo = d3.timeMonth.offset(latestDate, -24);

            const currentVals = filtered
                .filter(d => boroughs.has(d.borough))
                .filter(d => d.date > oneYearAgo && d.date <= latestDate)
                .map(d => d.metric_value_pct);

            const previousVals = filtered
                .filter(d => boroughs.has(d.borough))
                .filter(d => d.date > twoYearsAgo && d.date <= oneYearAgo)
                .map(d => d.metric_value_pct);

            if (previousVals.length === 0) return null;

            const currentAvg = d3.mean(currentVals);
            const previousAvg = d3.mean(previousVals);

            return ((currentAvg - previousAvg) / previousAvg) * 100;
        }



        function updateSummaryPills() {

            const boroughs = activeBoroughs.size > 0
                ? activeBoroughs
                : new Set(crimeData.map(d => d.borough));

            const dateDomain = currentXDomain || fullXDomain;

            const crimeTotal = computeCrimeTotal(crimeData, boroughs, dateDomain);
            const percAvg = computePerceptionAvg(perceptionData, boroughs, dateDomain, selectedMetric);
            const crimeChange = computeCrime12MonthChange(crimeData, boroughs);
            const percChange = computePerc12MonthChange(perceptionData, boroughs, selectedMetric);

            // MAIN VALUES
            d3.select("#crime-summary-value").text(crimeTotal.toLocaleString());
            d3.select("#perc-summary-value").text(percAvg ? percAvg.toFixed(1) + "%" : "–");

            // RESET CHANGE PILL CLASSES
            d3.select("#crime-change-value").attr("class", "change-value");
            d3.select("#perc-change-value").attr("class", "change-value");

            // CRIME CHANGE ARROW LOGIC
            if (crimeChange != null) {
                const arrow = crimeChange >= 0 ? "▲" : "▼";
                const colorClass = crimeChange >= 0 ? "arrow-up-red" : "arrow-down-green";
                d3.select("#crime-change-value")
                    .attr("class", `change-value ${colorClass}`)
                    .text(`${arrow} ${Math.abs(crimeChange).toFixed(1)}%`);
            }

            // PERCEPTION CHANGE ARROW LOGIC
            if (percChange != null) {
                const arrow = percChange >= 0 ? "▲" : "▼";
                const colorClass = percChange >= 0 ? "arrow-up-green" : "arrow-down-red";
                d3.select("#perc-change-value")
                    .attr("class", `change-value ${colorClass}`)
                    .text(`${arrow} ${Math.abs(percChange).toFixed(1)}%`);
            }
        }


        // SHOW THE MOST RECENT CRIME AND PERCEPTION VALUES IN THE HOVERLIST
        function showLatestValues(showDate = true) {
            if (activeBoroughs.size === 0) {
                // ⭐ Compute latestDate from ALL crime data
                latestDate = d3.max(crimeData, d => d.date);
                // Hoverlist should show instructional message
                updateHoverList(null, [], null);
                return;
            }
            // 1. Build latest crime values for each active borough
            const crimeLatest = Array.from(activeBoroughs).map(borough => {
                const arr = crimeDataByBorough.get(borough);
                if (!arr || arr.length === 0) return { borough, crime: null };

                const last = arr[arr.length - 1];   // last monthly crime row
                return {
                    borough,
                    crime: last.crime_count
                };
            });

            // 2. Build latest perception values for each active borough
            const percLatest = Array.from(activeBoroughs).map(borough => {
                const arr = percDataByBorough.get(borough);
                if (!arr || arr.length === 0) return { borough, perception: null };

                const last = arr[arr.length - 1];   // last quarterly perception row
                return {
                    borough,
                    perception: last.metric_value_pct
                };
            });
            // 3. Latest RESIDUAL values
            const residualLatest = Array.from(activeBoroughs).map(borough => {
                const arr = residualDataByBorough.get(borough);
                if (!arr || arr.length === 0) return { borough, residual: null };

                const last = arr[arr.length - 1];
                return {
                    borough,
                    residual: last.residual
                };
            });

            // 3. Merge crime + perception into unified rows
            const mergedLatest = mergeCrimeAndPerception(
                residualLatest,
                crimeLatest,
                percLatest
            );

            // 4. Update dashboard-level hover data
            latestResidualHoverData = residualLatest;
            latestCrimeHoverData = crimeLatest;
            latestPerceptionHoverData = percLatest;

            // 5. Latest date for display (use crime latest date)
            latestDate = d3.max(
                Array.from(activeBoroughs).map(b => {
                    const arr = crimeDataByBorough.get(b);
                    return arr && arr.length ? arr[arr.length - 1].date : null;
                })
            );
            // 6. Update hoverList
            updateHoverList(latestDate, mergedLatest, true);

            // 7. Update choromap to latest quarter
            if (latestDate) {
                choroMap.updateMapForQuarter(latestDate);
            }
        }

        // update the hoverlist
        // Unified hover-list renderer (HEADLINES COLUMN REMOVED).
// Call: updateHoverList(date, mergedRowsArray, pinnedBoolean)
// mergedRowsArray: [{ borough | crime_type, crime?, perception?, residual? }, ...]
        function updateHoverList(date, mergedRows = [], pinned = false, options = {}) {
            // date: Date or null
            // mergedRows: array of { crime_type | borough, crime, perception, residual }
            // pinned: boolean (if true, keep scroll position)
            // options: { containerSelector, colorScale, maxCrime, residualExtent, width }

            // Title / date display
            const titleNode = d3.select("#hover-list-title");
            if (titleNode.empty()) {
                // create if missing
                d3.select("#hoverList").insert("div", ":first-child")
                    .attr("id", "hover-list-title")
                    .attr("class", "hover-list-title");
            }
            if (date) {
                const fmt = d3.timeFormat("%B %Y");
                d3.select("#hover-list-title").text(fmt(date));
            } else {
                d3.select("#hover-list-title").text("Latest values");
            }

            // Update selectedHoverRow visual state (caller should set selectedHoverRow variable)
            if (typeof selectedHoverRow !== "undefined") {
                d3.select("#hover-list-rows").selectAll(".hover-row").classed("selected-hover-row", d => {
                    // d may be undefined on initial render; use dataset key fallback
                    const key = (d && (d.crime_type ?? d.borough ?? d.key)) || d3.select(this).node()?.dataset?.key;
                    return key === selectedHoverRow;
                });
            }

            // Render rows
            renderHoverList(mergedRows, {
                containerSelector: options.containerSelector,
                colorScale: typeof crimeColor !== "undefined" ? crimeColor : null,
                maxCrime: options.maxCrime,
                residualExtent: options.residualExtent,
                width: options.width
            });

            // Scroll behavior
            const rowsNode = document.getElementById("hover-list-rows");
            if (rowsNode && !pinned) rowsNode.scrollTop = 0;
        }


        ///////////////////////////////////////////////////////////////////////
        // INCLUDE HIGHLIGHT LOGIC
        ///////////////////////////////////////////////////////////////////////

        // ONLY PLACE WHERE HOVER STATE CHANGES
        function setHoverBorough(boroughName) {
            hoverBorough = boroughName;
            updateDashboardHoverState();
        }

        function setHoverQuarter(q) {
            hoverQuarter = q;
            updateDashboardHoverState();
        }

        function onHeatmapHoverCell(borough, date) {
            // 1. Set hover state FIRST
            hoverBorough = borough;
            hoverQuarter = date;

            // 2. Update dashboard
            updateDashboardHoverState();

            // 1. VISUAL heatmap highlight (row + column + cell)
            heatmapModule.highlightCell(borough, date);

            // 2. Update hover state AFTER highlight
            hoverBorough = borough;
            hoverQuarter = date;

            // 5. Build residual hover data
            const residualHoverData = Array.from(activeBoroughs).map(b => {
                const arr = residualDataByBorough.get(b);
                const row = arr?.find(d => d.date.getTime() === date.getTime());
                // const row = arr?.find(r => r.date.getTime() === date.getTime());
                return { borough: b, residual: row ? row.residual : null };
            });

            // 3. Build crime hover data for this quarter
            const crimeHoverData = Array.from(activeBoroughs).map(b => {
                const arr = crimeDataByBorough.get(b);
                const row = arr?.find(d => d.date.getTime() === date.getTime());
                return {
                    borough: b,
                    crime: row ? row.crime_count : null
                };
            });

            // 4. Build perception hover data for this quarter
            const percHoverData = Array.from(activeBoroughs).map(b => {
                const arr = percDataByBorough.get(b);
                const row = arr?.find(d => d.date.getTime() === date.getTime());
                return {
                    borough: b,
                    perception: row ? row.metric_value_pct : null
                };
            });

            // 5. Merge using your existing function
            const mergedHoverData = mergeCrimeAndPerception(
                residualHoverData,
                crimeHoverData,
                percHoverData
            );

            // 6. Update dashboard-level hover data
            latestResidualHoverData = residualHoverData;
            latestCrimeHoverData = crimeHoverData;
            latestPerceptionHoverData = percHoverData;

            // 7. Update hover list
            updateHoverList(date, mergedHoverData, true);

            // 8. Update choromap
            choroMap.updateMapForQuarter(date);

            // 9. Move hoverline
            const snappedX = x(date);
            hoverLineResidual.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
            hoverLineCrime.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
            hoverLinePerc.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
        }

        // drawMicroBarsForRow (headline column removed)
        function drawMicroBarsForRow(rowNode, item, scales, colorScale) {
            // rowNode: DOM element for the row
            // item: { crime_type | borough, crime, perception, residual }
            // scales: { crime, crimeCap, perception, residual, width }
            const w = scales.width || 80;

            // CRIME microbar
            const svgC = rowNode.querySelector(".metric.crime svg");
            if (svgC) {
                svgC.innerHTML = "";
                if (item.crime == null) {
                    svgC.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    const cap = scales.crimeCap || item.crime;
                    const width = Math.max(1, (scales.crime ? scales.crime(Math.min(item.crime, cap)) : Math.min(item.crime, w)));
                    const fill = (typeof colorScale === "function") ? colorScale(item.crime_type ?? item.borough) : "#666";
                    svgC.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${width}" height="8" fill="${fill}" rx="2"></rect>`);
                }
            }

            // PERCEPTION microbar (0..100)
            const svgP = rowNode.querySelector(".metric.perception svg");
            if (svgP) {
                svgP.innerHTML = "";
                if (item.perception == null) {
                    svgP.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    const val = Math.max(0, Math.min(100, item.perception));
                    const width = scales.perception ? scales.perception(val) : (val / 100) * w;
                    const fill = (typeof colorScale === "function") ? colorScale(item.crime_type ?? item.borough) : "#4a90e2";
                    svgP.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${width}" height="8" fill="${fill}" rx="2"></rect>`);
                }
            }

            // RESIDUAL microbar (centered at zero)
            const svgR = rowNode.querySelector(".metric.residual svg");
            if (svgR) {
                svgR.innerHTML = "";
                // residual scale maps domain -> [0, w]
                const residualScale = scales.residual || (v => (v + 1) * (w / 2));
                const zeroX = residualScale(0);
                svgR.insertAdjacentHTML("beforeend",
                    `<line x1="${zeroX}" x2="${zeroX}" y1="1" y2="11" stroke="rgba(0,0,0,0.12)" stroke-width="1"></line>`);

                if (item.residual == null) {
                    svgR.insertAdjacentHTML("beforeend",
                        `<rect x="0" y="2" width="${w}" height="8" fill="rgba(255,255,255,0.06)" rx="2"></rect>`);
                } else {
                    const valX = residualScale(item.residual);
                    if (item.residual < 0) {
                        const width = Math.abs(zeroX - valX);
                        svgR.insertAdjacentHTML("beforeend",
                            `<rect x="${valX}" y="2" width="${width}" height="8" fill="#e76f51" rx="2"></rect>`);
                    } else {
                        const width = Math.abs(valX - zeroX);
                        svgR.insertAdjacentHTML("beforeend",
                            `<rect x="${zeroX}" y="2" width="${width}" height="8" fill="#2a9d8f" rx="2"></rect>`);
                    }
                }
            }
        }

        // renderHoverList (HEADLINES REMOVED) — DOM-based renderer (no headlines column)
        function renderHoverList(mergedArray, options = {}) {
            const containerSelector = options.containerSelector || "#hover-list-rows";
            let container = document.querySelector(containerSelector);
            if (!container) {
                const parent = document.getElementById("hoverList");
                container = document.createElement("ul");
                container.id = "hover-list-rows";
                container.style.margin = 0;
                container.style.padding = 0;
                parent.appendChild(container);
            }

            const colorScale = options.colorScale || null;
            const w = options.width || 80;

            const scales = {
                width: w,
                crime: d3.scaleLinear().domain([0, Math.max(1, options.maxCrime || 1)]).range([0, w]),
                crimeCap: Math.max(1, options.maxCrime || 1),
                perception: d3.scaleLinear().domain([0, 100]).range([0, w]),
                residual: d3.scaleLinear().domain(options.residualExtent || d3.extent(mergedArray, d => d.residual) || [-1, 1]).range([0, w])
            };

            // Build map of existing nodes keyed by data key
            const existing = new Map();
            container.querySelectorAll(".hover-row").forEach(n => existing.set(n.dataset.key, n));

            const fragment = document.createDocumentFragment();

            mergedArray.forEach(item => {
                const key = item.crime_type ?? item.borough ?? item.key ?? item.name;
                const dataKey = String(key);
                let row = existing.get(dataKey);

                if (!row) {
                    row = document.createElement("li");
                    row.className = "hover-row";
                    row.dataset.key = dataKey;
                    row.setAttribute("role", "listitem");
                    row.tabIndex = 0;

                    row.innerHTML = `
        <div class="row-left">
          <span class="swatch" aria-hidden="true"></span>
          <span class="crime-name"></span>
        </div>
        <div class="row-values" role="group" aria-label="">
          <div class="metric crime"><svg width="${w}" height="12"></svg><div class="num crime-num"></div></div>
          <div class="metric perception"><svg width="${w}" height="12"></svg><div class="num perception-num"></div></div>
          <div class="metric residual"><svg width="${w}" height="12"></svg><div class="num residual-num"></div></div>
        </div>
      `;

                    // interactions
                    row.addEventListener("mouseenter", () => {
                        if (typeof setHoverCrimeType === "function") setHoverCrimeType(dataKey);
                        if (typeof setHoverBorough === "function") setHoverBorough(dataKey);
                        if (typeof highlightLine === "function") highlightLine(dataKey);
                    });
                    row.addEventListener("mouseleave", () => {
                        if (typeof setHoverCrimeType === "function") setHoverCrimeType(null);
                        if (typeof setHoverBorough === "function") setHoverBorough(null);
                        if (typeof clearHoverHighlight === "function") clearHoverHighlight();
                    });
                    row.addEventListener("click", () => {
                        if (typeof toggleActiveCrimeTypes === "function") toggleActiveCrimeTypes(dataKey);
                        if (typeof toggleActiveBorough === "function") toggleActiveBorough(dataKey);
                        // visually pin selection handled by updateHoverList caller via selectedHoverRow
                    });
                }

                // attach datum for d3 convenience
                d3.select(row).datum(item);

                // populate left
                const nameNode = row.querySelector(".crime-name");
                if (nameNode) nameNode.textContent = dataKey;

                const sw = row.querySelector(".swatch");
                if (sw) sw.style.background = (typeof colorScale === "function") ? colorScale(dataKey) : "#999";

                // populate numbers using formatters if available
                const crimeNum = row.querySelector(".crime-num");
                if (crimeNum) crimeNum.textContent = (typeof fmtInt === "function") ? fmtInt(item.crime) : (item.crime != null ? item.crime : "-");

                const percNum = row.querySelector(".perception-num");
                if (percNum) percNum.textContent = (typeof fmtPct === "function") ? fmtPct(item.perception) : (item.perception != null ? (Math.round(item.perception * 100) / 100) + "%" : "-");

                const residNum = row.querySelector(".residual-num");
                if (residNum) residNum.textContent = (typeof fmtResidual === "function") ? fmtResidual(item.residual) : (item.residual != null ? (Math.round(item.residual * 100) / 100) : "-");

                // accessibility label
                const ariaParts = [
                    dataKey,
                    `Crime ${item.crime == null ? "missing" : ((typeof fmtInt === "function") ? fmtInt(item.crime) : item.crime)}`,
                    `Perception ${item.perception == null ? "missing" : ((typeof fmtPct === "function") ? fmtPct(item.perception) : ((Math.round(item.perception * 100) / 100) + "%"))}`,
                    `Residual ${item.residual == null ? "missing" : ((typeof fmtResidual === "function") ? fmtResidual(item.residual) : item.residual)}`
                ];
                const rowValues = row.querySelector(".row-values");
                if (rowValues) rowValues.setAttribute("aria-label", ariaParts.join(", "));

                // draw micro bars
                drawMicroBarsForRow(row, item, scales, colorScale);

                fragment.appendChild(row);
                existing.delete(dataKey);
            });

            // remove leftover nodes
            existing.forEach(n => n.remove());

            container.appendChild(fragment);
        }

        function setupTrendToggle() {
            const btn = document.getElementById("toggleTrendBtn");
            const crimeChart = document.getElementById("chart-crime");
            const perceptionChart = document.getElementById("chart-perception");
            const crimeTitle = document.getElementById("crime-title");
            const perceptionTitle = document.getElementById("perception-title");
            const residualChart = document.getElementById("chart-residual");
            const residualTitle = document.getElementById("residual-title");

            // Defensive checks
            if (!btn) return;

            // Initial state: crime & perception visible; residual hidden
            const ensureVisible = (el) => {
                if (!el) return;
                el.classList.remove("hidden-chart");
                el.classList.add("visible-chart");
            };
            const ensureHidden = (el) => {
                if (!el) return;
                el.classList.remove("visible-chart");
                el.classList.add("hidden-chart");
            };

            ensureVisible(crimeChart);
            ensureVisible(perceptionChart);
            ensureVisible(crimeTitle);
            ensureVisible(perceptionTitle);

            ensureHidden(residualChart);
            ensureHidden(residualTitle);

            // Button initial label
            btn.textContent = "Show Residual Chart";

            // Track residual visibility
            let residualVisible = false;

            btn.addEventListener("click", () => {
                residualVisible = !residualVisible;

                if (residualVisible) {
                    // Show residual chart + title
                    btn.textContent = "Hide Residual Chart";
                    if (residualChart) {
                        residualChart.classList.remove("hidden-chart");
                        residualChart.classList.add("visible-chart");
                    }
                    if (residualTitle) {
                        residualTitle.classList.remove("hidden-chart");
                        residualTitle.classList.add("visible-chart");
                    }
                } else {
                    // Hide residual chart + title
                    btn.textContent = "Show Residual Chart";
                    if (residualChart) {
                        residualChart.classList.remove("visible-chart");
                        residualChart.classList.add("hidden-chart");
                    }
                    if (residualTitle) {
                        residualTitle.classList.remove("visible-chart");
                        residualTitle.classList.add("hidden-chart");
                    }
                }
            });
        }
        setupTrendToggle();


        function updateDashboardActiveState() {

            crimeChart.updateActiveBoroughs(activeBoroughs);
            perceptionChart.updateActiveBoroughs(activeBoroughs);
            residualChart.updateActiveBoroughs(activeBoroughs);
            choroMap.updateActiveBoroughs(activeBoroughs);
            heatmapModule.updateActiveBoroughs(activeBoroughs);

            showLatestValues(true);

        }

        // This is the central hover controller.
        // Every module calls setHoverBorough() on hover.
        function updateDashboardHoverState() {

            const hoverListSel = d3.select("#hoverList");

            // --------------------------------------------------
            // 0. Determine the date to display
            // --------------------------------------------------
            const displayDate = hoverQuarter ? hoverQuarter : latestDate;
            const monthYear = displayDate ? d3.timeFormat("%B %Y")(displayDate) : "";

            // --------------------------------------------------
            // 1. HoverList row highlight
            // --------------------------------------------------
            if (hoverBorough && activeBoroughs.size > 0) {
                hoverListSel.selectAll(".hover-row")
                    .classed("selected-hover-row", r => r.borough === hoverBorough);
            } else {
                hoverListSel.selectAll(".hover-row")
                    .classed("selected-hover-row", false);
            }

            // --------------------------------------------------
            // 2. Line chart hover highlight
            // --------------------------------------------------
            if (hoverBorough) {
                crimeChart.highlightLine(hoverBorough);
                perceptionChart.highlightLine(hoverBorough);
                residualChart.highlightLine(hoverBorough);
                choroMap.highlightArea(hoverBorough);
                hoverLineCrime.raise();
                hoverLinePerc.raise();
                hoverLineResidual.raise();
            } else {
                crimeChart.clearHoverHighlight();
                perceptionChart.clearHoverHighlight();
                residualChart.clearHoverHighlight();
                choroMap.clearAreaHighlight();
            }

            // --------------------------------------------------
            // 3. Heatmap hover highlight
            // --------------------------------------------------
            if (hoverQuarter && hoverBorough) {
                heatmapModule.highlightCell(hoverBorough, hoverQuarter);
            } else if (hoverQuarter && !hoverBorough) {
                heatmapModule.highlightCell(null, hoverQuarter);
            } else if (hoverBorough && !hoverQuarter) {
                heatmapModule.highlightRow(hoverBorough);
            } else {
                heatmapModule.clearHoverHighlight();
                heatmapModule.clearCellHover();
            }

            // --------------------------------------------------
            // 4. Choromap title (always depends ONLY on displayDate)
            // --------------------------------------------------
            // need this title shifted down a bit
            d3.select("#choro-map-title")
                .html(`
            Showing Crime Count and Perception % count divergence in London for
            <div style="text-align:center; font-size:1.3em; font-weight:700; margin-top:4px;">
                ${monthYear}
            </div>
        `);
            console.log(hoverQuarter);
            // --------------------------------------------------
            // 5. Hoverlist title (depends on active boroughs AND hoverQuarter)
            // --------------------------------------------------

            if (activeBoroughs.size === 0) {
                d3.select("#hover-list-title")
                    .html(`Select Crime Types <br> To See a Summary of Selected Crime Categories`);
            } else if (hoverQuarter) {
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
            if (hoverQuarter) {
                const snappedX = x(hoverQuarter);
                hoverLineCrime.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
                hoverLinePerc.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);
                hoverLineResidual.attr("x1", snappedX).attr("x2", snappedX).style("opacity", 1);

                hoverLineCrime.raise();
                hoverLinePerc.raise();
                hoverLineResidual.raise();
            } else {
                hoverLineCrime.style("opacity", 0);
                hoverLinePerc.style("opacity", 0);
                hoverLineResidual.style("opacity", 0);
            }

            // --------------------------------------------------
            // 7. Choromap recolor
            // --------------------------------------------------
            choroMap.updateMetric(selectedMetric);
            choroMap.updateMapForQuarter(displayDate);
        }
        updateDashboardHoverState();


        ///////////////////////////////////////////////////////////////////////
        // INCLUDE ZOOM/BRUSHING LOGIC
        ///////////////////////////////////////////////////////////////////////

        ///////////////////////////////////////////////////////////////////////
        // INCLUDE X-axis scaling LOGIC after zoom/brush
        ///////////////////////////////////////////////////////////////////////

        ///////////////////////////////////////////////////////////////////////
        // INCLUDE LEGEND BUILDING LOGIC:
        ///////////////////////////////////////////////////////////////////////


        //ENSURE BOROUGH NAMESS MATCH CRIME AND PERCEPTION DATASETS



    }).catch(err => {
        console.error("DATA LOAD ERROR:", err);
    });
}
