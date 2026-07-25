// perception linechart for perception vs crime (borough)
// Updated to mirror the crime-type module's domain/redraw behavior but grouped by borough.
export function drawPerceptionChart({
                                        container,
                                        data,
                                        x,
                                        y,
                                        width,
                                        height,
                                        margin,
                                        color,
                                        activeBoroughs,
                                        setHoverBorough,
                                        onLineHover,
                                        onLineClick,
                                        onZoom,
                                    }) {
    console.log("PERCEPTION linechart js is running (boroughs)");

    let activeBoroughsSet = new Set();
    let cachedByBorough = null;

    const chartContainer = d3.select(container);

    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height);

    let innerWidth = width - margin.left - margin.right;
    let innerHeight = height - margin.top - margin.bottom;

    // clip region
    svg.append("defs")
        .append("clipPath")
        .attr("id", "perception-clip")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const plotGroup = chartGroup.append("g")
        .attr("clip-path", "url(#perception-clip)");

    const xAxis = chartGroup.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));

    const yAxis = chartGroup.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(y).tickFormat(d => d + "%"));

    const lineGen = d3.line()
        .defined(d => d && d.date && (d.metric_value_pct != null) && !isNaN(d.metric_value_pct))
        .x(d => x(d.date))
        .y(d => y(d.metric_value_pct));

    let boroughLines = null;

    const brush = d3.brushX()
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on("end", zoomIn);

    chartGroup.append("g")
        .attr("class", "zoom")
        .call(brush);

    dim(true);

    // ============================================================
    // INITIALIZE
    // ============================================================
    function initializePerceptionChart(selectedMetric) {
        // cache grouped data for the selected metric
        const filtered = data.filter(d => d.metric === selectedMetric);
        cachedByBorough = d3.group(filtered, d => d.borough);

        const boroughs = Array.from(cachedByBorough, ([k, v]) => {
            const sorted = v.slice().sort((a, b) => a.date - b.date);
            return [k, sorted];
        });

        if (color && typeof color.domain === "function") {
            color.domain(boroughs.map(d => d[0]));
        }

        // Draw all borough lines initially (mirrors crime-type module)
        boroughLines = plotGroup.selectAll(".perception-line")
            .data(boroughs, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "perception-line")
                    .attr("stroke", d => color(d[0]))
                    .attr("fill", "none")
                    .attr("d", d => lineGen(d[1]))
                    .on("mousemove", (event, d) => {
                        if (typeof setHoverBorough === "function") setHoverBorough(d[0]);
                        if (typeof onLineHover === "function") onLineHover(d[0]);
                    })
                    .on("mouseout", () => {
                        if (typeof setHoverBorough === "function") setHoverBorough(null);
                        if (typeof onLineHover === "function") onLineHover(null);
                    })
                    .on("click", (event, d) => {
                        if (typeof onLineClick === "function") onLineClick(d[0]);
                    }),

                update => update
                    .attr("stroke", d => color(d[0]))
                    .attr("d", d => lineGen(d[1])),

                exit => exit.remove()
            );
    }

    // ============================================================
    // COMPUTE Y DOMAIN (min fixed at 0, max based on active set or all)
    // ============================================================
    function computeYDomain(activeSet) {
        const byB = cachedByBorough || d3.group(data, d => d.borough);
        const boroughsToConsider = (activeSet && activeSet.size > 0)
            ? Array.from(activeSet)
            : Array.from(byB.keys());

        let maxVal = 0;
        for (const b of boroughsToConsider) {
            const arr = byB.get(b);
            if (!arr) continue;
            for (const r of arr) {
                const val = +r.metric_value_pct || 0;
                if (val > maxVal) maxVal = val;
            }
        }

        if (maxVal === 0) return [0, 1];
        // keep percent scale: return [0, max * 1.1]
        return [0, maxVal * 1.1];
    }

    // ============================================================
    // REDRAW LINES (mirrors crime-type redrawLines with domain tween)
    // ============================================================
    function redrawLines() {
        // Ensure cached grouping exists (use full data if not cached)
        cachedByBorough = cachedByBorough || d3.group(data, d => d.borough);

        const byBorough = cachedByBorough;
        const boroughs = Array.from(byBorough, ([k, v]) => {
            const sorted = v.slice().sort((a, b) => a.date - b.date);
            return [k, sorted];
        });

        // Update color domain
        if (color && typeof color.domain === "function") {
            color.domain(boroughs.map(d => d[0]));
        }

        // Data join
        boroughLines = plotGroup.selectAll(".perception-line")
            .data(boroughs, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "perception-line")
                    .attr("stroke", d => color(d[0]))
                    .attr("fill", "none")
                    // collapsed start for animation
                    .attr("d", d => {
                        const last = d[1][d[1].length - 1];
                        return lineGen([last, last]);
                    })
                    .style("cursor", d => typeof onLineClick === "function" ? "pointer" : "default")
                    .on("mousemove", (event, d) => {
                        if (typeof setHoverBorough === "function") setHoverBorough(d[0]);
                        if (typeof onLineHover === "function") onLineHover(d[0]);
                    })
                    .on("mouseout", () => {
                        if (typeof setHoverBorough === "function") setHoverBorough(null);
                        if (typeof onLineHover === "function") onLineHover(null);
                    })
                    .on("click", (event, d) => {
                        if (typeof onLineClick === "function") onLineClick(d[0]);
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

        // Ensure active set exists
        if (!(activeBoroughsSet instanceof Set)) activeBoroughsSet = new Set();

        const newDomain = computeYDomain(activeBoroughsSet);
        const oldDomain = y.domain();

        if (oldDomain[0] === newDomain[0] && oldDomain[1] === newDomain[1]) {
            boroughLines
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("stroke-width", 2)
                .attr("d", d => lineGen(d[1]));

            redrawYAxis();
            return;
        }

        // TRANSITIONS FOR DOMAIN
        const t = d3.transition().duration(650).ease(d3.easeCubicInOut);
        const i0 = d3.interpolateNumber(oldDomain[0], newDomain[0]);
        const i1 = d3.interpolateNumber(oldDomain[1], newDomain[1]);

        t.tween("yDomain", () => {
            return function (tVal) {
                y.domain([i0(tVal), i1(tVal)]);
                plotGroup.selectAll(".perception-line").attr("d", d => lineGen(d[1]));
                redrawYAxis();
            };
        });

        boroughLines.transition(t).attr("stroke-width", 2);

        t.on("end", () => {
            const lines = plotGroup.selectAll(".perception-line");

            if (activeBoroughsSet.size === 0) {
                lines
                    .classed("active-highlight", false)
                    .classed("dimmed", false)
                    .classed("hover-highlight", false)
                    .classed("super-highlight", false);
                dim(true);
                lines.lower();
                return;
            }

            dim(false);

            lines
                .classed("active-highlight", d => activeBoroughsSet.has(d[0]))
                .classed("dimmed", d => !activeBoroughsSet.has(d[0]))
                .classed("hover-highlight", false)
                .classed("super-highlight", false);

            lines.filter(d => activeBoroughsSet.has(d[0])).raise();
            lines.filter(d => !activeBoroughsSet.has(d[0])).lower();
        });
    }

    // ============================================================
    // ACTIVE SET UPDATE (mirrors crime-type updateActiveCrimeTypes)
    // ============================================================
    function updateActiveBoroughs(activeSet) {
        // Normalize and store active set inside module
        activeBoroughsSet = (activeSet instanceof Set) ? activeSet : new Set();

        // If lines not initialized yet, bail out
        if (!boroughLines) return;

        // Compute new y-domain based on active set
        const newDomain = computeYDomain(activeBoroughsSet);
        y.domain(newDomain);

        // Redraw axis + lines once
        redrawYAxis();
        redrawLines();

        // Fresh selection AFTER redraw (critical!)
        const lines = plotGroup.selectAll(".perception-line");

        // CASE: no active boroughs → clear highlight + dim chart
        if (!activeBoroughsSet || activeBoroughsSet.size === 0) {
            lines
                .classed("active-highlight", false)
                .classed("dimmed", false)
                .classed("hover-highlight", false)
                .classed("super-highlight", false);

            dim(true);      // dim whole chart
            lines.lower();  // ensure default ordering
            return;
        }

        // CASE: some boroughs selected → undim chart + apply classes
        dim(false);

        lines
            .classed("active-highlight", d => activeBoroughsSet.has(d[0]))
            .classed("dimmed", d => !activeBoroughsSet.has(d[0]))
            .classed("hover-highlight", false)
            .classed("super-highlight", false);

        // Raise active lines, lower inactive lines
        lines.filter(d => activeBoroughsSet.has(d[0])).raise();
        lines.filter(d => !activeBoroughsSet.has(d[0])).lower();
    }

    // ============================================================
    // Highlight / Clear hover
    // ============================================================
    function highlightLine(boroughName) {
        plotGroup.selectAll(".perception-line")
            .classed("hover-highlight", d => d[0] === boroughName)
            .filter(d => d[0] === boroughName)
            .raise();
    }

    function clearHoverHighlight() {
        plotGroup.selectAll(".perception-line")
            .classed("hover-highlight", false)
            .classed("super-highlight", false);
    }

    // ============================================================
    // Zoom / Axis helpers
    // ============================================================
    function zoomIn(event) {
        if (!event.sourceEvent) return;
        const selection = event.selection;
        if (!selection) return;

        const [x0, x1] = selection;
        const newDomain = [x.invert(x0), x.invert(x1)];

        if (typeof onZoom === "function") onZoom(newDomain);
        chartGroup.select(".zoom").call(brush.move, null);
    }

    function applyXDomain(domain) {
        x.domain(domain);
        redrawLines();
        redrawXAxis();
    }

    function redrawXAxis() {
        xAxis.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));
    }

    function redrawYAxis() {
        yAxis.transition().duration(600)
            .call(d3.axisLeft(y).tickFormat(d => d + "%"));
    }

    function dim(isDimmed) {
        d3.select(container).style("opacity", isDimmed ? 0.25 : 1);
    }

    // ============================================================
    // Public API
    // ============================================================
    return {
        initializePerceptionChart,
        updateData(newData) {
            // update internal data and re-cache grouping
            data = newData;
            cachedByBorough = null; // force re-group on next redraw
            redrawLines();
        },
        applyXDomain,
        redrawXAxis,
        redrawLines,
        plotGroupNode: plotGroup.node(),
        updateActiveBoroughs,
        highlightLine,
        clearHoverHighlight,
        dim
    };
} // end export
