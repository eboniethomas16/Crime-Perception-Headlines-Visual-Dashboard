// Borough heatmap module (remade from the "crime types" heatmap)
// Usage: drawHeatmap({ container, data, selectedMetric, activeBoroughs, setHoverBorough, setHoverQuarter, onHeatmapHoverCell, onClick })
export function drawHeatmap({
                                container,
                                data,
                                selectedMetric,
                                activeBoroughs,
                                setHoverBorough,
                                setHoverQuarter,
                                onHeatmapHoverCell,
                                onClick,
                                updateDashboardHoverState
                            }) {
    // -------------------------
    // Layout / sizing
    // -------------------------
    const containerNode = document.querySelector(container);
    if (!containerNode) throw new Error(`Container not found: ${container}`);

    const margin = { top: 20, right: 10, bottom: 80, left: 250 };
    // keep CSS var in sync with JS margin.left/top so CSS and JS don't drift
    document.documentElement.style.setProperty('--heatmap-left-width', `${margin.left}px`);
    // document.documentElement.style.setProperty('--heatmap-legend-width', `100px`);
    // document.documentElement.style.setProperty('--heatmap-legend-gap', `-20px`);

    function computeSize() {
        const cw = containerNode.clientWidth;
        const ch = containerNode.clientHeight;
        let width = cw;
        let height = ch;
        if (height < 300) height = 300;
        return { width, height };
    }

    const { width: initWidth, height: initHeight } = computeSize();
    const innerHeight = initHeight - margin.top - margin.bottom;
    const extraRightPadding = 60;
    const cellWidth = 40;

    // scales (populated in updateMetric)
    let x = null;
    let y = null;
    let currentDateDomain = null; // zoomed domain (optional)
    let firstRender = true;

    // -------------------------
    // DOM: wrapper, left column, scroll area
    // -------------------------
    let wrapper = d3.select(container).select("#heatmap-scroll-wrapper");
    if (wrapper.empty()) {
        wrapper = d3.select(container)
            .append("div")
            .attr("id", "heatmap-scroll-wrapper");
    } else {
        wrapper.html("");
    }

    // Left fixed column for borough labels
    const leftColumn = wrapper.append("div")
        .attr("id", "heatmap-left-column")
        .style("margin-left",
            `calc(var(--heatmap-legend-width) + var(--heatmap-legend-gap))`);

    // left fixed column for y axis
    const leftSvg = leftColumn.append("svg")
        .attr("width", 250)
        .attr("height", initHeight);

    // left group positioned at top margin
    const leftG = leftSvg.append("g")
        .attr("transform", `translate(0, ${margin.top})`);

    // y-axis group placed at x = 0 inside leftG; CSS can pin it to right edge if desired
    const yAxisGroupLeft = leftG.append("g")
        .attr("class", "y-axis")
        .attr("transform", `translate(${248}, 0)`);

    // Right scrollable area (heatmap + x-axis)
    const scrollDiv = wrapper.append("div")
        .attr("class", "heatmap-scroll-right")
        .style("overflow-x", "scroll")
        .style("overflow-y", "hidden")
        .style("flex", "1 1 auto")
        .attr("transform", `translate(${extraRightPadding}, 0)`);

    const innerSvg = scrollDiv.append("svg")
        .attr("height", initHeight)
        .style("display", "block");

    // group inside innerSvg: translate vertically only (no horizontal offset)
    const svgG = innerSvg.append("g")
        .attr("transform", `translate(${0}, ${margin.top})`);

    const xAxisGroup = svgG.append("g")
        .attr("class", "x-axis");

    const heatmapG = svgG.append("g")
        .attr("class", "heatmap-g");


    // Core update function, when perception
    // metric is changed, Controls row reordering
    function updateMetric(metric) {
        // filter rows for the selected metric
        const filtered = data.filter(d => d.metric === metric);

        // apply date domain if zoomed
        let filteredForDates = filtered;
        if (currentDateDomain) {
            const [d0, d1] = currentDateDomain;
            filteredForDates = filtered.filter(d => d.date >= d0 && d.date <= d1);
        }

        // Borough ordering by average hybrid_sjsd (descending)
        const boroughAverages = d3.rollup(
            filtered,
            v => d3.mean(v, d => d.hybrid_sjsd),
            d => d.borough
        );

        const boroughs = [...new Set(filteredForDates.map(d => d.borough))];
        boroughs.sort((a, b) => (boroughAverages.get(b) || 0) - (boroughAverages.get(a) || 0));

        // dates as numeric timestamps (consistent keys)
        const dates = [...new Set(filteredForDates.map(d => +d.date))].sort((a, b) => a - b);
        const formatDate = d3.timeFormat("%b %Y");

        // compute total width for scrollable svg
        const totalWidth = Math.max(1, dates.length) * cellWidth;
        innerSvg.attr("width", totalWidth + extraRightPadding + 20);

        // x scale: domain is numeric timestamps
        x = d3.scaleBand()
            .domain(dates)
            .range([0, totalWidth])
            .padding(0.02);

        // y scale: domain is borough names; use innerHeight so axis and rows align
        y = d3.scaleBand()
            .domain(boroughs)
            .range([0, innerHeight])
            .padding(0.0001);

        // color scale: diverging around 0 using hybrid_sjsd
        const maxAbs = d3.max(filtered, d => Math.abs(d.hybrid_sjsd)) || 1;
        const color = d3.scaleDiverging()
            .domain([-maxAbs, 0, maxAbs])
            .interpolator(d3.interpolateRdYlGn)
            .clamp(true);

        // X axis: place at innerHeight (so it's visible inside the svg)
        xAxisGroup
            .attr("transform", `translate(0, ${innerHeight})`)
            .call(d3.axisBottom(x).tickFormat(d => formatDate(new Date(+d))))
            .selectAll("text")
            .attr("transform", "rotate(-45)")
            .style("text-anchor", "end");

        // Left y-axis: call axisLeft with same y scale
        yAxisGroupLeft
            .transition()
            .duration(firstRender ? 0 : 800)
            .call(d3.axisLeft(y).tickSize(2))


        // add title attribute and optional truncation for long borough names
        yAxisGroupLeft.selectAll("text")
            .each(function (d) {
                const node = d3.select(this);
                const full = node.text();
                node.attr("title", full);
                const maxChars = 28;
                if (full.length > maxChars) node.text(full.slice(0, maxChars - 1) + "…");
            });

        // ROW JOIN
        const rows = heatmapG.selectAll(".heatmap-row")
            .data(boroughs, d => d);

        const rowsEnter = rows.enter()
            .append("g")
            .attr("class", "heatmap-row")
            .attr("transform", d => `translate(0, ${y(d)})`);

        // Merge + row-level hover handlers
        rowsEnter.merge(rows)
            .attr("transform", d => `translate(0, ${y(d)})`)
            .on("mouseenter", function (event, d) {
                if (typeof setHoverBorough === "function") setHoverBorough(d);
                if (typeof setHoverQuarter === "function") setHoverQuarter(null);
                heatmapG.selectAll(".heatmap-row").classed("hover-highlight", r => r === d);

            })
            .on("mouseleave", function () {
                if (typeof setHoverBorough === "function") setHoverBorough(null);
                if (typeof setHoverQuarter === "function") setHoverQuarter(null);
                heatmapG.selectAll(".heatmap-row").classed("hover-highlight", false);

            });

        rows.exit().remove();

        // CELL JOIN: bind by numeric date key (+d.date) for each row
        const rects = rowsEnter.merge(rows)
            .selectAll("rect")
            .data(borough => filteredForDates.filter(d => d.borough === borough), d => +d.date);

        // Enter
        const rectsEnter = rects.enter()
            .append("rect")
            .attr("x", d => x(+d.date))
            .attr("width", () => x.bandwidth())
            .attr("height", y.bandwidth() * 0.8)
            .attr("y", 0)
            .style("fill", d => color(d.hybrid_sjsd))
            .style("stroke", "white")
            .style("stroke-width", 1)
            .on("mouseenter", (event, d) => {
                if (typeof setHoverQuarter === "function") setHoverQuarter(d.date);
                if (typeof setHoverBorough === "function") setHoverBorough(d.borough);
                if (typeof onHeatmapHoverCell === "function") onHeatmapHoverCell(d.borough, d.date);
                heatmapG.selectAll(".heatmap-row").classed("hover-highlight", r => r === d.borough);
                heatmapG.selectAll("rect").classed("hover-column", r => +r.date === +d.date);
                d3.select(event.currentTarget).classed("hover-cell", true);
                updateDashboardHoverState();
            })
            .on("mouseleave", (event, d) => {
                if (typeof setHoverQuarter === "function") setHoverQuarter(null);
                if (typeof setHoverBorough === "function") setHoverBorough(null);
                if (typeof onHeatmapHoverCell === "function") onHeatmapHoverCell(null, null);
                clearCellHover();
                updateDashboardHoverState();
            })
            .on("click", (event, d) => {
                if (typeof onClick === "function") onClick(d.borough);
            });

        // Update + merge
        rectsEnter.merge(rects)
            .transition()
            .duration(firstRender ? 0 : 800)
            .attr("x", d => x(+d.date))
            .attr("width", () => x.bandwidth())
            .style("fill", d => color(d.hybrid_sjsd));

        rects.exit().remove();

        firstRender = false;
    }
    // sends information to the hover line
    // handler in the dashboard
    function updateDateDomain(domain) {
        currentDateDomain = domain;
        updateMetric(selectedMetric);
    }
    // update active borough when borough row is selected
    function updateActiveBoroughs(activeSet) {
        heatmapG.selectAll(".heatmap-row")
            .classed("active-row", d => activeSet.has(d))
            .classed("dimmed-row", d => activeSet.size > 0 && !activeSet.has(d));

        yAxisGroupLeft.selectAll("text")
            .classed("active-row", d => activeSet.has(d))
            .classed("dimmed-row", d => activeSet.size > 0 && !activeSet.has(d));
    }
    // Highlight the cell on mouse enter
    function highlightCell(borough, date) {
        heatmapG.selectAll("rect")
            .classed("hover-cell", d => d.borough === borough && +d.date === +date);

        heatmapG.selectAll(".heatmap-row")
            .classed("hover-highlight", d => d === borough);

        heatmapG.selectAll("rect")
            .classed("hover-column", d => +d.date === +date);
    }
    // Clear the cell hover when mouse leaves
    function clearCellHover() {
        heatmapG.selectAll(".hover-cell").classed("hover-cell", false);
        heatmapG.selectAll(".hover-column").classed("hover-column", false);
        heatmapG.selectAll(".hover-highlight").classed("hover-highlight", false);
    }
    // Highlight the borough row
    function highlightRow(boroughName) {
        heatmapG.selectAll(".heatmap-row")
            .classed("hover-highlight", d => d === boroughName);
        yAxisGroupLeft.selectAll("text")
            .classed("hover-highlight", d => d === boroughName);
    }
    // Clear Highlights across the dashboard
    function clearHoverHighlight() {
        heatmapG.selectAll(".hover-highlight").classed("hover-highlight", false);
        heatmapG.selectAll(".hover-cell").classed("hover-cell", false);
        heatmapG.selectAll(".hover-column").classed("hover-column", false);
        yAxisGroupLeft.selectAll("text").classed("hover-highlight", false);
    }
    // initial render
    updateMetric(selectedMetric);
    // Return API
    return {
        updateMetric,
        updateActiveBoroughs,
        highlightRow,
        clearHoverHighlight,
        highlightCell,
        clearCellHover,
        updateDateDomain,
        onHeatmapHoverCell,
    };
}
