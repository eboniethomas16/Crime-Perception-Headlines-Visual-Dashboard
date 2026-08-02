// Residual linechart for Crime vs Perception (boroughs)
export function drawResidualChart({
                                      container,
                                      aggregatedResiduals,   // ONE LINE (array of {date, residual})
                                      boroughResiduals,      // MANY LINES (array of {borough, date, residual})
                                      x,
                                      width,
                                      height,
                                      margin,
                                      color,
                                      activeBoroughs,
                                      setHoverBorough,
                                      onLineHover,
                                      onLineClick,
                                      onZoom
                                  }) {

    console.log("Residual linechart module running (boroughs)");

    let activeBoroughsSet = new Set();

    const chartContainer = d3.select(container);

    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height);

    let innerWidth  = width  - margin.left - margin.right;
    let innerHeight = height - margin.top  - margin.bottom;

    // Clip region
    svg.append("defs")
        .append("clipPath")
        .attr("id", "clip-residual-borough")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const plotGroup = chartGroup.append("g")
        .attr("clip-path", "url(#clip-residual-borough)");

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
    const xLabel = chartGroup.append("text")
        .attr("class", "axis-label axis-label-x")
        .attr("text-anchor", "middle")
        .attr("fill", "#222")
        .style("font-family", "Poppins, sans-serif")
        .style("font-size", "12px")
        .text("Date");

    const yAxis = chartGroup.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(y));
    const yLabel = chartGroup.append("text")
        .attr("class", "axis-label axis-label-y")
        .attr("text-anchor", "middle")
        .attr("fill", "#222")
        .style("font-family", "Poppins, sans-serif")
        .style("font-size", "12px")
        .text("Residual (Obs. - Pred.)");

    // -----------------------------
    // LINE GENERATORS
    // -----------------------------
    const lineGen = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.residual));

    let aggregatedLine;
    let boroughLines;

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

        // animate initial aggregated path
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

        // start with no borough lines
        boroughLines = plotGroup.selectAll(".residual-line")
            .data([])
            .join(); // do not create empty paths
        positionAxisLabels()
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
    // REDRAW LINES (agg + borough)
    // -----------------------------
    function redrawLines() {

        // Always redraw aggregated line datum (path will be updated during tween)
        aggregatedLine.datum(aggregatedResiduals);



        // If no boroughs selected → reset y-domain to aggregated only and remove lines
        if (!activeBoroughsSet || activeBoroughsSet.size === 0) {
            const minR = d3.min(aggregatedResiduals, d => d.residual);
            const maxR = d3.max(aggregatedResiduals, d => d.residual);

            // Immediately set domain for aggregated-only view
            y.domain([minR, maxR]).nice();
            yAxis.call(d3.axisLeft(y));

            plotGroup.selectAll(".residual-line").remove();
            boroughLines = plotGroup.selectAll(".residual-line").data([]);

            zeroLine
                .attr("x1", x.range()[0])
                .attr("x2", x.range()[1])
                .attr("y1", y(0))
                .attr("y2", y(0));

            // ensure aggregated path uses the new scale
            aggregatedLine.attr("d", lineGen(aggregatedResiduals));
            return;
        }

        // Group residuals by borough and build activeData
        const byBorough = d3.group(boroughResiduals, d => d.borough);
        const activeData = Array.from(activeBoroughsSet)
            .map(b => [b, byBorough.get(b)])
            .filter(([b, arr]) => Array.isArray(arr) && arr.length > 0);

        // Compute new y-domain from aggregated + active boroughs
        const allResiduals = aggregatedResiduals.concat(...activeData.map(d => d[1]));
        const newMin = d3.min(allResiduals, d => d.residual);
        const newMax = d3.max(allResiduals, d => d.residual);

        // --- Enter / Update / Exit with transitions ---
        boroughLines = plotGroup.selectAll(".residual-line")
            .data(activeData, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "residual-line")
                    .attr("stroke", d => color(d[0]))
                    .attr("stroke-width", 3)            // start thicker for enter
                    .attr("fill", "none")
                    // collapsed start using the series' last point
                    .attr("d", d => {
                        const arr = d[1];
                        const last = arr[arr.length - 1];
                        return lineGen([last, last]);
                    })
                    .on("mousemove", (event, d) => { if (typeof onLineHover === "function") onLineHover(d[0]); })
                    .on("mouseout", () => { if (typeof onLineHover === "function") onLineHover(null); })
                    .on("click", (event, d) => { if (typeof onLineClick === "function") onLineClick(d[0]); }),

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

        // --- Animate domain change with tweening ---
        const oldDomain = y.domain();
        const newDomain = [newMin, newMax];

        // Fast path: identical domain
        if (oldDomain[0] === newDomain[0] && oldDomain[1] === newDomain[1]) {
            boroughLines
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("stroke-width", 2)
                .attr("d", d => lineGen(d[1]));

            aggregatedLine
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("d", lineGen(aggregatedResiduals));

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

        const t = d3.transition().duration(650).ease(d3.easeCubicInOut);
        const i0 = d3.interpolateNumber(oldDomain[0], newDomain[0]);
        const i1 = d3.interpolateNumber(oldDomain[1], newDomain[1]);

        t.tween("yDomain", () => {
            return function (tVal) {
                y.domain([i0(tVal), i1(tVal)]);
                plotGroup.selectAll(".residual-line").attr("d", d => lineGen(d[1]));
                aggregatedLine.attr("d", lineGen(aggregatedResiduals));
                yAxis.call(d3.axisLeft(y));
                zeroLine.attr("y1", y(0)).attr("y2", y(0));
            };
        });

        boroughLines.transition(t).attr("stroke-width", 2);
        aggregatedLine.transition(t).attr("d", lineGen(aggregatedResiduals));
    }

    // -----------------------------
    // ACTIVE BOROUGH STYLING
    // -----------------------------
    function updateActiveBoroughs(activeSet) {
        activeBoroughsSet = activeSet;

        // CASE: no boroughs selected
        if (!activeSet || activeSet.size === 0) {
            plotGroup.selectAll(".residual-line").remove();
            boroughLines = plotGroup.selectAll(".residual-line").data([]);
            aggregatedLine
                .classed("dimmed-aggregated", false)
                .classed("aggregated-residual-line", true)
                .raise();

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

        // CASE: boroughs selected
        redrawLines();

        aggregatedLine
            .classed("dimmed-aggregated", true)
            .classed("aggregated-residual-line", true);

        // Styling for borough lines
        boroughLines
            .classed("active-highlight", true)
            .classed("dimmed", false)
            .classed("hover-highlight", false);

        boroughLines.raise();
        aggregatedLine.lower();
    }

    function highlightLine(boroughName) {
        boroughLines
            .classed("hover-highlight", d => d[0] === boroughName)
            .filter(d => d[0] === boroughName)
            .raise();
    }

    function clearHoverHighlight() {
        boroughLines.classed("hover-highlight", false);
    }

    // -----------------------------
    // UPDATE DATA (metric change)
    // -----------------------------
    function updateData({ aggregated, borough }) {
        aggregatedResiduals = aggregated;
        boroughResiduals = borough;

        // recompute y-domain across all series
        const allResiduals = aggregated.concat(borough);
        const minR = d3.min(allResiduals, d => d.residual);
        const maxR = d3.max(allResiduals, d => d.residual);

        y.domain([minR, maxR]).nice();
        yAxis.call(d3.axisLeft(y));

        zeroLine
            .attr("x1", x.range()[0])
            .attr("x2", x.range()[1])
            .attr("y1", y(0))
            .attr("y2", y(0));

        redrawLines();
    }
    function positionAxisLabels() {
        xLabel.attr("x", innerWidth / 2).attr("y", innerHeight + 40);
        yLabel.attr("x", -innerHeight / 2).attr("y", -margin.left + 14).attr("transform", `rotate(-90)`);
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
        updateActiveBoroughs,
        highlightLine,
        clearHoverHighlight,
        dim
    };
}
