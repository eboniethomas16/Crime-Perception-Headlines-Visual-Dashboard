// Headline dash
export function drawResidualChart({
                                               container,
                                               aggregatedResiduals,   // ONE LINE
                                               crimeTypeResiduals,    // MANY LINES
                                               x,
                                               width,
                                               height,
                                               margin,
                                               color,
                                               activeCrimeTypes,
                                               setHoverCrimeType,
                                               onLineHover,
                                               onLineClick,
                                               onZoom
                                           }) {

    console.log("Residual Crime-Type linechart module running");

    let activeCrimeTypesSet = new Set();

    const chartContainer = d3.select(container);

    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height);

    let innerWidth  = width  - margin.left - margin.right;
    let innerHeight = height - margin.top  - margin.bottom;

    // Clip region
    svg.append("defs")
        .append("clipPath")
        .attr("id", "clip-residual-crimetype")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const plotGroup = chartGroup.append("g")
        .attr("clip-path", "url(#clip-residual-crimetype)");

    const zeroLine = plotGroup.append("line")
        .attr("class", "zero-baseline");

    // -----------------------------
    // Y‑DOMAIN (initial = aggregated only)
    // -----------------------------
    let minResidual = d3.min(aggregatedResiduals, d => d.residual);
    let maxResidual = d3.max(aggregatedResiduals, d => d.residual);

    let y = d3.scaleLinear()
        .domain([minResidual, maxResidual])
        .range([innerHeight, 0])
        .nice();

    // -----------------------------
    // AXES
    // -----------------------------
    const xAxis = chartGroup.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));

    const yAxis = chartGroup.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(y));

    // -----------------------------
    // LINE GENERATORS
    // -----------------------------
    const lineGen = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.residual));

    let aggregatedLine;
    let crimeTypeLines;

    // -----------------------------
    // BRUSH FOR ZOOM
    // -----------------------------
    const brush = d3.brushX()
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on("end", zoomIn);

    chartGroup.append("g")
        .attr("class", "zoom")
        .call(brush);

    // -----------------------------
    // INITIAL DRAW (AGGREGATED ONLY)
    // -----------------------------
    function initializeResidualChart() {

        aggregatedLine = plotGroup.append("path")
            .datum(aggregatedResiduals)
            .attr("class", "aggregated-residual-line")
            .attr("fill", "none")
            .attr("d", lineGen);

        aggregatedLine
            .call(line => line.transition()
                .duration(600)
                .attr("d", lineGen(aggregatedResiduals))
            );


        zeroLine
            .attr("x1", x.range()[0])
            .attr("x2", x.range()[1])
            .attr("y1", y(0))
            .attr("y2", y(0));

        crimeTypeLines = plotGroup.selectAll(".residual-line")
            .data([])
            .join();   // ⭐ do NOT create empty paths

    }

    // -----------------------------
    // ZOOM HANDLER
    // -----------------------------
    function zoomIn(event) {
        if (!event.sourceEvent) return;
        const selection = event.selection;
        if (!selection) return;

        const [x0, x1] = selection;
        const newDomain = [x.invert(x0), x.invert(x1)];

        onZoom(newDomain);

        chartGroup.select(".zoom").call(brush.move, null);
    }

    // -----------------------------
    // APPLY X‑DOMAIN
    // -----------------------------
    function applyXDomain(domain) {
        x.domain(domain);
        redrawLines();
        redrawXAxis();
    }

    function redrawXAxis() {
        xAxis.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));
    }

    // -----------------------------
    // REDRAW LINES (agg + crime types)
    // -----------------------------
    function redrawLines() {

        // Always redraw aggregated line datum (path will be updated during tween)
        aggregatedLine.datum(aggregatedResiduals);

        // If no crime types selected → reset y-domain to aggregated only and remove lines
        if (!activeCrimeTypesSet || activeCrimeTypesSet.size === 0) {
            const minR = d3.min(aggregatedResiduals, d => d.residual);
            const maxR = d3.max(aggregatedResiduals, d => d.residual);

            // Immediately set domain for aggregated-only view
            y.domain([minR, maxR]).nice();
            yAxis.call(d3.axisLeft(y));

            plotGroup.selectAll(".residual-line").remove();
            crimeTypeLines = plotGroup.selectAll(".residual-line").data([]);

            zeroLine
                .attr("x1", x.range()[0])
                .attr("x2", x.range()[1])
                .attr("y1", y(0))
                .attr("y2", y(0));

            // ensure aggregated path uses the new scale
            aggregatedLine.attr("d", lineGen(aggregatedResiduals));
            return;
        }

        // Group residuals by crimeType and build activeData
        const byCrimeType = d3.group(crimeTypeResiduals, d => d.crime_type);
        const activeData = Array.from(activeCrimeTypesSet)
            .map(ct => [ct, byCrimeType.get(ct)])
            .filter(([ct, arr]) => Array.isArray(arr) && arr.length > 0);

        // Compute new y-domain from aggregated + active crime types
        const allResiduals = aggregatedResiduals.concat(...activeData.map(d => d[1]));
        const newMin = d3.min(allResiduals, d => d.residual);
        const newMax = d3.max(allResiduals, d => d.residual);

        // --- Enter / Update / Exit (no nested transitions here) ---
        crimeTypeLines = plotGroup.selectAll(".residual-line")
            .data(activeData, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "residual-line")
                    .attr("stroke", d => color(d[0]))
                    .attr("stroke-width", 3)            // start thicker
                    .attr("fill", "none")
                    // collapsed start using current (old) y scale at the series' last date
                    .attr("d", d => {
                        const last = d[1][d[1].length - 1];
                        return lineGen([last, last]);
                    }),

                update => update
                    .attr("stroke", d => color(d[0]))
                    .attr("fill", "none"),

                exit => exit
                    .style("opacity", 1)
                    .call(exitSel => exitSel.transition()
                        .duration(350)
                        .ease(d3.easeCubicInOut)
                        .style("opacity", 0)
                        .remove()
                    )
            );

        // --- Animate domain and redraw everything per frame ---
        // Capture old domain
        const oldDomain = y.domain();
        const newDomain = [newMin, newMax];

        // If domain is identical, just transition paths (fast path)
        if (oldDomain[0] === newDomain[0] && oldDomain[1] === newDomain[1]) {
            // simple path transition for enter+update
            crimeTypeLines
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("stroke-width", 2)
                .attr("d", d => lineGen(d[1]));

            // aggregated line update
            aggregatedLine
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("d", lineGen(aggregatedResiduals));

            // baseline and axis update (no domain change)
            zeroLine
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("y1", y(0))
                .attr("y2", y(0));

            yAxis
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .call(d3.axisLeft(y));

            return;
        }

        // Create a transition and tween the domain; on each tick update paths and axis
        const t = d3.transition().duration(650).ease(d3.easeCubicInOut);

        // Interpolators for domain endpoints
        const i0 = d3.interpolateNumber(oldDomain[0], newDomain[0]);
        const i1 = d3.interpolateNumber(oldDomain[1], newDomain[1]);

        // Use a tween on the transition to update the scale and redraw
        t.tween("yDomain", () => {
            return function (tVal) {
                // update y domain for this frame
                y.domain([i0(tVal), i1(tVal)]);
                // redraw all series paths using the interpolated scale
                plotGroup.selectAll(".residual-line").attr("d", d => lineGen(d[1]));
                aggregatedLine.attr("d", lineGen(aggregatedResiduals));
                // update axis and baseline
                yAxis.call(d3.axisLeft(y));
                zeroLine.attr("y1", y(0)).attr("y2", y(0));
            };
        });

        // Also animate stroke-width settling for enter/update
        crimeTypeLines
            .transition(t)
            .attr("stroke-width", 2);

        // Ensure aggregated line finishes with final path (in case)
        aggregatedLine.transition(t).attr("d", lineGen(aggregatedResiduals));
    }



    // -----------------------------
    // ACTIVE CRIME TYPE STYLING
    // -----------------------------
    function updateActiveCrimeTypes(activeSet) {
        activeCrimeTypesSet = activeSet;   // ⭐ store inside module
        // CASE 1: No crime types selected
        if (!activeSet || activeSet.size === 0) {

            // Remove crime-type residual lines
            plotGroup.selectAll(".residual-line").remove();
            crimeTypeLines = plotGroup.selectAll(".residual-line").data([]);

            // Aggregated line returns to normal (not dimmed)
            aggregatedLine
                .classed("dimmed-aggregated", false)
                .classed("aggregated-residual-line", true)
                .raise();

            // Dim chart
            dim(true);

            // Reset y-domain to aggregated only
            const minR = d3.min(aggregatedResiduals, d => d.residual);
            const maxR = d3.max(aggregatedResiduals, d => d.residual);
            y.domain([minR, maxR]).nice();
            yAxis.call(d3.axisLeft(y));

            zeroLine
                .attr("x1", x.range()[0])
                .attr("x2", x.range()[1])
                .attr("y1", y(0))
                .attr("y2", y(0));

            return;
        }


        // CASE 2: Crime types selected
        redrawLines();

        aggregatedLine
            .classed("dimmed-aggregated", true)
            .classed("aggregated-residual-line", true);

        // Undim chart
        dim(false);

        const byCrimeType = d3.group(crimeTypeResiduals, d => d.crime_type);

        const crimeTypes = Array.from(activeSet)
            .map(ct => [ct, byCrimeType.get(ct)])
            .filter(([ct, arr]) => Array.isArray(arr) && arr.length > 0);



        crimeTypeLines
            .classed("active-highlight", true)
            .classed("dimmed", false)
            .classed("hover-highlight", false);

        crimeTypeLines.raise();
        aggregatedLine.lower();
    }


    function highlightLine(crimeTypeName) {
        crimeTypeLines
            .classed("hover-highlight", d => d[0] === crimeTypeName)
            .filter(d => d[0] === crimeTypeName)
            .raise();
    }

    function clearHoverHighlight() {
        crimeTypeLines.classed("hover-highlight", false);
    }

    // -----------------------------
    // UPDATE DATA (metric change)
    // -----------------------------
    function updateData({ aggregated, crimeTypes }) {

        aggregatedResiduals = aggregated;
        crimeTypeResiduals = crimeTypes;

        redrawLines();
    }
    function dim(isDimmed) {
        d3.select(container)
            .style("opacity", isDimmed ? 0.25 : 1);
    }

    return {
        initializeResidualChart,
        updateData,
        applyXDomain,
        redrawXAxis,
        redrawLines,
        plotGroupNode: plotGroup.node(),
        updateActiveCrimeTypes,
        highlightLine,
        clearHoverHighlight,
        dim
    };
}
