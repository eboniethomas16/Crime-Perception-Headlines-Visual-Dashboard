// Crime types heatmap module (modeled on borough heatmap)
export function drawHeadlineHeatmap({
                                         container,
                                         data,
                                         activeCrimeTypes,
                                         setHoverCrimeType,
                                         setHoverDate,
                                         onHeatmapHoverCell,
                                         onClick,
                                        updateDashboardHoverState,

                                     }) {
    // DOM container
    const containerNode = document.querySelector(container);
    if (!containerNode) throw new Error(`Container not found: ${container}`);

    const margin = { top: 20, right: 10, bottom: 120, left: 170 };
    const leftColumnWidth = margin.left; // single source of truth for left column width

    // keep CSS var in sync with JS margin.left/top so CSS and JS don't drift
    document.documentElement.style.setProperty('--heatmap-left-width', `${margin.left}px`);
    // document.documentElement.style.setProperty('--heatmap-legend-width', `0px`);
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
        .attr("width", leftColumnWidth)
        .attr("height", initHeight)
        .style("display", "block");

    const leftG = leftSvg.append("g")
        .attr("transform", `translate(0, ${margin.top})`);

    const yAxisGroupLeft = leftG.append("g")
        .attr("class", "y-axis")
        .attr("transform", `translate(${leftColumnWidth - 8}, 0)`);


    // Right scrollable area (heatmap + x-axis)
    const scrollDiv = wrapper.append("div")
        .attr("class", "heatmap-scroll-right")
        .style("overflow-x", "scroll")
        .style("overflow-y", "hidden")
        .style("flex", "1 1 auto")
        .style("min-width", "0");


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
    // core update function
    function updateMetric() {
        // filter rows for the selected metric
        // let filteredForDates = filtered;

        // apply date domain if zoomed
        let filteredForDates = data;
        if (currentDateDomain) {
            const [d0, d1] = currentDateDomain;
            filteredForDates = data.filter(d => d.date >= d0 && d.date <= d1);
        }

        // Borough ordering by average hybrid_sjsd (descending)
        const crimeTypeAverages = d3.rollup(
            data,
            v => d3.mean(v, d => d.signed_jsd),
            d => d.crime_type
        );

        let crimeTypes = [...new Set(data.map(d => d.crime_type))];
        crimeTypes.sort((a, b) => (crimeTypeAverages.get(b) || 0) - (crimeTypeAverages.get(a) || 0));
        crimeTypes = crimeTypes.map(t =>
            t === "MISCELLANEOUS CRIMES AGAINST SOCIETY" ? "MISCELLANEOUS C.A.M." : t
        );


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

        // y scale: domain is crime_type names; use innerHeight so axis and rows align
        y = d3.scaleBand()
            .domain(crimeTypes)
            .range([0, innerHeight])
            .padding(0.0001);

        // color scale: diverging around 0 using hybrid_sjsd
        const maxAbs = d3.max(data, d => Math.abs(d.signed_jsd)) || 1;
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
            .attr("transform", `translate(${leftColumnWidth - 8}, 0)`) // leftG already translated by margin.top

        // add title attribute and optional truncation for long crime type names
        yAxisGroupLeft.selectAll("text")
            .each(function (d) {
                const node = d3.select(this);
                const full = node.text();
                node.attr("title", full);
                const maxChars = 28;
                if (full.length > maxChars) node.text(full.slice(0, maxChars - 1) + "…");
            });


        // heatmapG.attr("transform", `translate(0, ${margin.top})`);


        // ROW JOIN
        const rows = heatmapG.selectAll(".heatmap-row")
            .data(crimeTypes, d => d);

        const rowsEnter = rows.enter()
            .append("g")
            .attr("class", "heatmap-row")
            .attr("transform", d => `translate(0, ${y(d)})`);

        // Merge + row-level hover handlers
        rowsEnter.merge(rows)
            .attr("transform", d => `translate(0, ${y(d)})`)
            .on("mouseenter", function (event, d) {
                if (typeof setHoverCrimeType === "function") setHoverCrimeType(d);
                if (typeof setHoverDate === "function") setHoverDate(null);
                heatmapG.selectAll(".heatmap-row").classed("hover-highlight", r => r === d);

            })
            .on("mouseleave", function () {
                if (typeof setHoverCrimeType === "function") setHoverCrimeType(null);
                if (typeof setHoverDate === "function") setHoverDate(null);
                heatmapG.selectAll(".heatmap-row").classed("hover-highlight", false);

            });

        rows.exit().remove();

        // CELL JOIN: bind by numeric date key (+d.date) for each row
        const rects = rowsEnter.merge(rows)
            .selectAll("rect")
            .data(crimeType => filteredForDates.filter(d => d.crime_type === crimeType), d => +d.date);

        // Enter
        const rectsEnter = rects.enter()
            .append("rect")
            .attr("x", d => x(+d.date))
            .attr("width", () => x.bandwidth())
            .attr("height", y.bandwidth() * 0.8)
            .attr("y", 0)
            .style("fill", d => color(d.signed_jsd))
            .style("stroke", "white")
            .style("stroke-width", 1)
            .on("mouseenter", (event, d) => {
                if (typeof setHoverDate === "function") setHoverDate(d.date);
                if (typeof setHoverCrimeType === "function") setHoverCrimeType(d.crime_type);
                if (typeof onHeatmapHoverCell === "function") onHeatmapHoverCell(d.crime_type, d.date);
                heatmapG.selectAll(".heatmap-row").classed("hover-highlight", r => r === d.crime_type);
                heatmapG.selectAll("rect").classed("hover-column", r => +r.date === +d.date);
                d3.select(event.currentTarget).classed("hover-cell", true);
                updateDashboardHoverState();

            })
            .on("mouseleave", (event, d) => {
                if (typeof setHoverDate === "function") setHoverDate(null);
                if (typeof setHoverCrimeType === "function") setHoverCrimeType(null);
                if (typeof onHeatmapHoverCell === "function") onHeatmapHoverCell(null, null);
                clearCellHover();
                updateDashboardHoverState();

            })
            .on("click", (event, d) => {
                if (typeof onClick === "function") onClick(d.crime_type);
            });

        // Update + merge
        rectsEnter.merge(rects)
            .transition()
            .duration(firstRender ? 0 : 800)
            .attr("x", d => x(+d.date))
            .attr("width", () => x.bandwidth())
            .style("fill", d => color(d.signed_jsd));

        rects.exit().remove();

        firstRender = false;
    }



    // API helpers
    function updateDateDomain(domain) {
        currentDateDomain = domain;
        updateMetric();
    }

    function updateActiveCrimeTypes(activeSet) {
        heatmapG.selectAll(".heatmap-row")
            .classed("active-row", d => activeSet.has(d))
            .classed("dimmed-row", d => activeSet.size > 0 && !activeSet.has(d));

        yAxisGroupLeft.selectAll("text")
            .classed("active-row", d => activeSet.has(d))
            .classed("dimmed-row", d => activeSet.size > 0 && !activeSet.has(d));
    }

    function highlightCell(crimeType, date) {
        heatmapG.selectAll("rect")
            .classed("hover-cell", d => d.crime_type === crimeType && +d.date === +date);

        heatmapG.selectAll(".heatmap-row")
            .classed("hover-highlight", d => d === crimeType);

        heatmapG.selectAll("rect")
            .classed("hover-column", d => +d.date === +date);
    }

    function clearCellHover() {
        heatmapG.selectAll(".hover-cell").classed("hover-cell", false);
        heatmapG.selectAll(".hover-column").classed("hover-column", false);
        heatmapG.selectAll(".hover-highlight").classed("hover-highlight", false);
    }

    function highlightRow(crimeTypeName) {
        heatmapG.selectAll(".heatmap-row").classed("hover-highlight", d => d === crimeTypeName);
        yAxisGroupLeft.selectAll("text").classed("hover-highlight", d => d === crimeTypeName);
    }

    function clearHoverHighlight() {
        heatmapG.selectAll(".hover-highlight").classed("hover-highlight", false);
        heatmapG.selectAll(".hover-cell").classed("hover-cell", false);
        heatmapG.selectAll(".hover-column").classed("hover-column", false);
        yAxisGroupLeft.selectAll("text").classed("hover-highlight", false);
    }

    // initial render
    updateMetric();

    return {
        updateMetric,
        updateActiveCrimeTypes,
        highlightRow,
        clearHoverHighlight,
        highlightCell,
        clearCellHover,
        updateDateDomain,
        onHeatmapHoverCell
    };
}
