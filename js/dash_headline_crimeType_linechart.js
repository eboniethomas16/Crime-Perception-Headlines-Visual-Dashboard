export function drawHeadlineChart({
                                      container,
                                      data,
                                      x,
                                      y,
                                      width,
                                      height,
                                      margin = { top: 20, right: 20, bottom: 40, left: 60 },
                                      color,
                                      onLineClick,
                                      onZoom,
                                      useDuplicates = false,
                                        onHoverCrimeType
                                  }) {
    let useDuplicatesState = !!useDuplicates;
    let activeCrimeTypesSet = new Set();
    let cachedByType = null;
    const tooltip = d3.select("#chart-headlines-tooltip");
    // helper to format month/quarter
    // const formatMonthYear = d3.timeFormat("%b %Y");

    function countField() {
        return useDuplicatesState ? "total_duplicate_headline_count" : "total_headline_count";
    }

    function setUseDuplicates(checked) {
        useDuplicatesState = !!checked;
        // recompute y domain for the current active set and redraw axis/lines
        const domain = computeYDomain(activeCrimeTypesSet);
        y.domain(domain);
        redrawYAxis();
        redrawLines();
    }

    const chartContainer = d3.select(container);
    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height);

    let innerWidth = width - margin.left - margin.right;
    let innerHeight = height - margin.top - margin.bottom;

    const safeId = (container || "headline").replace(/[^a-zA-Z0-9\-_]/g, "_");
    const clipId = `clip-headline-${safeId}`;

    svg.append("defs")
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const plotGroup = chartGroup.append("g")
        .attr("clip-path", `url(#${clipId})`);

    const xAxis = chartGroup.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));

    const yAxis = chartGroup.append("g")
        .attr("class", "y-axis")
        .call(
            d3.axisLeft(y)
                .ticks(6)
                .tickFormat(d3.format(","))
        );

    // Line generator uses dynamic count field
    const lineGen = d3.line()
        .defined(d => d && d.date && !isNaN(+d[countField()]))
        .x(d => x(d.date))
        .y(d => y(+d[countField()]));

    let headlineLines = null;

    const brush = d3.brushX()
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on("end", zoomIn);

    chartGroup.append("g")
        .attr("class", "zoom")
        .call(brush);

    // ============================================================
    // INITIALIZE
    // ============================================================
    function initializeHeadlineChart() {
        // cache grouped data for performance
        cachedByType = d3.group(data, d => d.crime_type);

        const crimeTypes = Array.from(cachedByType, ([k, v]) => {
            const sorted = v.slice().sort((a, b) => a.date - b.date);
            return [k, sorted];
        });

        if (color && typeof color.domain === "function") {
            color.domain(crimeTypes.map(d => d[0]));
        }



        headlineLines = plotGroup.selectAll(".headline-line")
            .data(crimeTypes, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "headline-line")
                    .attr("stroke", d => color ? color(d[0]) : "#333")
                    .attr("fill", "none")
                    .attr("d", d => lineGen(d[1]))
                    .style("cursor", d => typeof onLineClick === "function" ? "pointer" : "default")
                    .on("click", (event, d) => {
                        if (typeof onLineClick === "function") onLineClick(d[0]);
                    }),
                update => update
                    .attr("stroke", d => color ? color(d[0]) : "#333")
                    .attr("d", d => lineGen(d[1])),
                exit => exit.remove()
            );

        const overlay = plotGroup.append("rect")
            .attr("width", innerWidth)
            .attr("height", innerHeight)
            .style("fill", "none")
            .style("pointer-events", "all");

        overlay.on("mousemove", (event) => {
            const [mx, my] = d3.pointer(event);
            const crimeType = findNearestCrimeType(mx, my);

            if (crimeType) {
                showHoverTooltip(crimeType, event);
                if (typeof onHoverCrimeType === "function") onHoverCrimeType(crimeType);
            } else {
                hideHoverTooltip();
                if (typeof onHoverCrimeType === "function") onHoverCrimeType(null);
            }
        });

        overlay.on("mouseleave", hideHoverTooltip);


    }




    // ============================================================
    // ACTIVE HIGHLIGHT
    // ============================================================
    function updateActiveCrimeTypes(activeSet) {
        activeCrimeTypesSet = (activeSet instanceof Set) ? activeSet : new Set();

        // if lines not initialized yet, keep the set and return
        if (!headlineLines) return;

        // compute and apply new y domain based on activeSet
        const newDomain = computeYDomain(activeCrimeTypesSet);
        y.domain(newDomain);

        // redraw axis and lines once
        redrawYAxis();
        redrawLines();

        // fresh selection after redraw
        const lines = plotGroup.selectAll(".headline-line");

        // CASE: no crime types selected -> clear highlighting / dim chart
        if (!activeCrimeTypesSet || activeCrimeTypesSet.size === 0) {
            lines
                .classed("active-highlight", false)
                .classed("dimmed", false)
                .classed("hover-highlight", false)
                .classed("super-highlight", false);

            dim(true);
            lines.lower();
            return;
        }

        // CASE: some crime types selected -> undim chart and apply classes
        dim(false);

        lines
            .classed("active-highlight", d => activeCrimeTypesSet.has(d[0]))
            .classed("dimmed", d => activeCrimeTypesSet.size > 0 && !activeCrimeTypesSet.has(d[0]))
            .classed("hover-highlight", false)
            .classed("super-highlight", false);

        lines.filter(d => activeCrimeTypesSet.has(d[0])).raise();
        lines.filter(d => !activeCrimeTypesSet.has(d[0])).lower();
    }

    function highlightLine(crimeTypeName) {
        if (!headlineLines) return;
        if (!crimeTypeName) {
            plotGroup.selectAll(".headline-line").classed("hover-highlight", false);
            return;
        }
        plotGroup.selectAll(".headline-line")
            .classed("hover-highlight", d => d[0] === crimeTypeName)
            .filter(d => d[0] === crimeTypeName)
            .raise();
    }

    function clearHoverHighlight() {
        plotGroup.selectAll(".headline-line")
            .classed("hover-highlight", false)
            .classed("super-highlight", false);
    }

    function setSelectedCrimeType(selectedCrimeType, activeSet) {
        if (!headlineLines) return;
        if (!activeSet || activeSet.size === 0) {
            plotGroup.selectAll(".headline-line")
                .classed("active-highlight", false)
                .classed("dimmed", false)
                .classed("hover-highlight", false)
                .classed("super-highlight", false);
            return;
        }

        plotGroup.selectAll(".headline-line")
            .classed("super-highlight", d => d[0] === selectedCrimeType)
            .classed("active-highlight", d => activeSet.has(d[0]) || d[0] === selectedCrimeType)
            .classed("dimmed", d => activeSet.size > 0 && !activeSet.has(d[0]) && d[0] !== selectedCrimeType);

        plotGroup.selectAll(".headline-line").filter(d => d[0] === selectedCrimeType).raise();
        plotGroup.selectAll(".headline-line").filter(d => !activeSet.has(d[0]) && d[0] !== selectedCrimeType).lower();
    }

    // ============================================================
    // ZOOM handler
    // ============================================================
    function zoomIn(event) {
        if (!event.sourceEvent) return;
        const selection = event.selection;
        if (!selection) return;
        const [x0, x1] = selection;
        const newDomain = [x.invert(x0), x.invert(x1)];
        onZoom(newDomain);
        chartGroup.select(".zoom").call(brush.move, null);
    }

    function applyXDomain(domain) {
        x.domain(domain);
        redrawLines();
        redrawXAxis();
    }

    function redrawXAxis() {
        chartGroup.select(".x-axis")
            .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));
    }

    function redrawYAxis() {
        chartGroup.select(".y-axis")
            .transition().duration(600)
            .call(
                d3.axisLeft(y)
                    .ticks(6)
                    .tickFormat(d3.format(","))
            );
    }

    // compute y domain from counts (respects useDuplicatesState)
    function computeYDomain(activeSet) {
        // use cachedByType if available
        const byType = cachedByType || d3.group(data, d => d.crime_type);
        const typesToConsider = (activeSet && activeSet.size > 0)
            ? Array.from(activeSet)
            : Array.from(byType.keys());

        let maxVal = 0;
        for (const t of typesToConsider) {
            const arr = byType.get(t);
            if (!arr) continue;
            for (const r of arr) {
                const val = +r[countField()] || 0;
                if (val > maxVal) maxVal = val;
            }
        }

        if (maxVal === 0) return [0, 1];
        return [0, maxVal * 1.1];
    }

    // ============================================================
    // REDRAW LINES
    // ============================================================
    function redrawLines() {
        const byType = cachedByType || d3.group(data, d => d.crime_type);
        const crimeTypes = Array.from(byType, ([k, v]) => {
            const sorted = v.slice().sort((a, b) => a.date - b.date);
            return [k, sorted];
        });

        

        // ENTER / UPDATE / EXIT
        headlineLines = plotGroup.selectAll(".headline-line")
            .data(crimeTypes, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "headline-line")
                    .attr("stroke", d => color ? color(d[0]) : "#333")
                    .attr("fill", "none")
                    // collapsed start (animate outward)
                    .attr("d", d => {
                        const last = d[1][d[1].length - 1];
                        return lineGen([last, last]);
                    })
                    .style("cursor", d => typeof onLineClick === "function" ? "pointer" : "default")
                    .on("click", (event, d) => {
                        if (typeof onLineClick === "function") onLineClick(d[0]);
                    }),

                update => update
                    .attr("stroke", d => color ? color(d[0]) : "#333")
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
        if (!(activeCrimeTypesSet instanceof Set)) activeCrimeTypesSet = new Set();

        // Compute new domain
        const newDomain = computeYDomain(activeCrimeTypesSet);
        const oldDomain = y.domain();

        // If domain unchanged → simple path transition
        if (oldDomain[0] === newDomain[0] && oldDomain[1] === newDomain[1]) {
            headlineLines
                .transition()
                .duration(650)
                .ease(d3.easeCubicInOut)
                .attr("stroke-width", 2)
                .attr("d", d => lineGen(d[1]));

            redrawYAxis();
            return;
        }

        // Domain tween transition
        const t = d3.transition().duration(650).ease(d3.easeCubicInOut);
        const i0 = d3.interpolateNumber(oldDomain[0], newDomain[0]);
        const i1 = d3.interpolateNumber(oldDomain[1], newDomain[1]);

        t.tween("yDomain", () => {
            return function (tVal) {
                y.domain([i0(tVal), i1(tVal)]);

                // redraw paths during tween
                plotGroup.selectAll(".headline-line")
                    .attr("d", d => lineGen(d[1]));

                redrawYAxis();
            };
        });

        // Animate stroke-width settling
        headlineLines.transition(t).attr("stroke-width", 2);

        // Apply active/dim classes AFTER tween
        t.on("end", () => {
            const lines = plotGroup.selectAll(".headline-line");

            if (activeCrimeTypesSet.size === 0) {
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
                .classed("active-highlight", d => activeCrimeTypesSet.has(d[0]))
                .classed("dimmed", d => !activeCrimeTypesSet.has(d[0]))
                .classed("hover-highlight", false)
                .classed("super-highlight", false);

            lines.filter(d => activeCrimeTypesSet.has(d[0])).raise();
            lines.filter(d => !activeCrimeTypesSet.has(d[0])).lower();
        });

        plotGroup.selectAll(".headline-line-group").raise();
    }


    function superHighlightLine(crimeTypeName) {
        if (!headlineLines) return;
        headlineLines
            .classed("super-highlight", d => d[0] === crimeTypeName)
            .filter(d => d[0] === crimeTypeName)
            .raise();
    }

    function dim(isDimmed) {
        d3.select(container)
            .style("opacity", isDimmed ? 0.25 : 1);
    }

    function findNearestCrimeType(mouseX, mouseY) {
        let nearest = null;
        let minDist = Infinity;

        headlineLines.each(function(d) {
            const crimeType = d[0];
            const values = d[1];

            // find the closest point in this line to the mouse X
            const date = x.invert(mouseX);
            const row = values.find(v => v.date.getTime() === date.getTime());
            if (!row) return;

            const yVal = y(row.total_headline_count);
            const dist = Math.abs(mouseY - yVal);

            if (dist < minDist) {
                minDist = dist;
                nearest = crimeType;
            }
        });

        return nearest;
    }


// show tooltip for a single crime type at a snapped date
    // show a tiny label with only the crime type (optional date/value ignored)
    function showHoverTooltip(crimeType, event) {
        tooltip
            .html(`<div style="font-weight:600">${crimeType}</div>`)
            .style("display", "block")
            .style("opacity", 1)
            .style("left", `${Math.max(padding, Math.min(window.innerWidth - 220, x))}px`)
            .style("top", `${Math.max(padding, Math.min(window.innerHeight - 40, y))}px`)
            .attr("aria-hidden", "false");
    }

    function hideHoverTooltip() {
        tooltip.style("display", "none").attr("aria-hidden", "true");
    }


    return {
        initializeHeadlineChart,
        applyXDomain,
        redrawXAxis,
        redrawLines,
        plotGroupNode: plotGroup.node(),
        xScale: x,
        updateActiveCrimeTypes,
        highlightLine,
        clearHoverHighlight,
        setUseDuplicates,
        showHoverTooltip,
        hideHoverTooltip,
        dim
    };
}
